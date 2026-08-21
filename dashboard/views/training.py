from django.utils import timezone

from ._shared import (
    Driver,
    DriverDrillCompletion,
    DriverTrainingCompletion,
    annual_drill,
    annual_training,
    driver_tool_box_meeting_attended,
    get_object_or_404,
    logger,
    messages,
    redirect,
    render,
    reverse,
    superuser_required,
    tool_box_meeting_topics,
    transaction,
    Http404,
    HttpResponseRedirect,
)

# Maps the URL-facing "kind" string to everything the bulk-mark views need
# to work generically across Training / Drill / TBM without three copies
# of the same view logic.
BULK_MARK_KINDS = {
    "training": {
        "label": "Training",
        "model": annual_training,
        "item_label_field": "train_name",
        "requires_date": True,
    },
    "drill": {
        "label": "Drill",
        "model": annual_drill,
        "item_label_field": "drill_name",
        "requires_date": True,
    },
    "tbm": {
        "label": "Tool Box Meeting",
        "model": tool_box_meeting_topics,
        "item_label_field": "meeting_topic",
        "requires_date": False,
    },
}


def _get_kind_or_404(kind):
    config = BULK_MARK_KINDS.get(kind)
    if config is None:
        raise Http404("Unknown bulk-mark type.")
    return config


@superuser_required
@transaction.atomic
def add_driver_training(request, D_ID):
    driver = get_object_or_404(Driver, D_ID=D_ID)
    drills = annual_drill.objects.all()
    training = annual_training.objects.all()

    if request.method == "POST":
        train_id = request.POST.get("train")
        drill_id = request.POST.get("drill")
        completed_date = request.POST.get("date")

        training_obj = get_object_or_404(annual_training, pk=train_id)
        drill_obj = get_object_or_404(annual_drill, pk=drill_id)

        DriverTrainingCompletion.objects.update_or_create(
            driver=driver,
            training=training_obj,
            defaults={"completed_date": completed_date},
        )
        DriverDrillCompletion.objects.update_or_create(
            driver=driver,
            drill=drill_obj,
            defaults={"completed_date": completed_date},
        )

        return HttpResponseRedirect(reverse("driverview", args=[D_ID]))

    return render(
        request,
        "training/add_training.html",
        {
            "driver": driver,
            "drills": drills,
            "training": training,
        },
    )


@superuser_required
@transaction.atomic
def add_tbm(request, D_ID):
    driver = get_object_or_404(Driver, D_ID=D_ID)
    tbm = tool_box_meeting_topics.objects.all()
    try:
        if request.method == "POST":
            meeting_topic = request.POST.get("meeting_topic")
            tbm_obj = tool_box_meeting_topics.objects.get(meeting_topic=meeting_topic)
            existing_record = driver_tool_box_meeting_attended.objects.filter(
                meeting_attended_by=driver, meetings_attended=tbm_obj
            ).first()
            if existing_record is None:
                tool = driver_tool_box_meeting_attended(
                    meeting_attended_by=driver,
                    meetings_attended=tbm_obj,
                    no_of_times_meeting_attended=1,
                )
                tool.save()
            else:
                existing_record.no_of_times_meeting_attended += 1
                existing_record.save()
            driver_view_url = reverse("driverview", args=[D_ID])
            return HttpResponseRedirect(driver_view_url)
        else:
            context = {"driver": driver, "tbms": tbm}
            return render(request, "tbm/add_tbm.html", context)
    except Exception as e:
        logger.exception("Operation failed in %s", request.path)
        messages.error(
            request, "Something went wrong. Please check your input and try again."
        )
        return redirect(request.path)


@superuser_required
def bulk_mark_select(request):
    """
    Step 1 of the bulk-mark wizard: pick WHAT is being marked
    (a specific Training / Drill / TBM topic, plus a date if applicable).
    """
    kind = request.GET.get("kind", "training")
    if kind not in BULK_MARK_KINDS:
        kind = "training"

    context = {
        "kinds": BULK_MARK_KINDS,
        "selected_kind": kind,
        "training_items": annual_training.objects.all(),
        "drill_items": annual_drill.objects.all(),
        "tbm_items": tool_box_meeting_topics.objects.all(),
        "today": timezone.localdate().isoformat(),
    }
    return render(request, "training/bulk_mark_select.html", context)


@superuser_required
def bulk_mark_drivers(request):
    """
    Step 2 of the bulk-mark wizard: shows every driver with a searchable,
    checkbox-selectable list, and on POST marks the chosen item as
    completed/attended for every selected driver in one transaction.
    """
    kind = request.GET.get("kind") or request.POST.get("kind")
    config = _get_kind_or_404(kind)
    item_id = request.GET.get("item") or request.POST.get("item")
    item_obj = get_object_or_404(config["model"], pk=item_id)
    completed_date = request.GET.get("date") or request.POST.get("date")

    if config["requires_date"] and not completed_date:
        messages.error(request, "Please choose a completion date.")
        return redirect(reverse("bulk_mark_select") + f"?kind={kind}")

    if request.method == "POST":
        driver_ids = request.POST.getlist("driver_ids")
        if not driver_ids:
            messages.error(request, "Select at least one driver to mark.")
            return redirect(request.get_full_path())

        drivers = list(Driver.objects.filter(D_ID__in=driver_ids))

        with transaction.atomic():
            if kind == "training":
                records = [
                    DriverTrainingCompletion(
                        driver=d, training=item_obj, completed_date=completed_date
                    )
                    for d in drivers
                ]
                DriverTrainingCompletion.objects.bulk_create(
                    records,
                    update_conflicts=True,
                    unique_fields=["driver", "training"],
                    update_fields=["completed_date"],
                )
            elif kind == "drill":
                records = [
                    DriverDrillCompletion(
                        driver=d, drill=item_obj, completed_date=completed_date
                    )
                    for d in drivers
                ]
                DriverDrillCompletion.objects.bulk_create(
                    records,
                    update_conflicts=True,
                    unique_fields=["driver", "drill"],
                    update_fields=["completed_date"],
                )
            else:  # tbm — increments an attendance counter, so it's not a
                   # straightforward "insert or overwrite" upsert; handled
                   # per-driver but still inside one atomic transaction.
                existing = {
                    rec.meeting_attended_by_id: rec
                    for rec in driver_tool_box_meeting_attended.objects.filter(
                        meetings_attended=item_obj, meeting_attended_by__in=drivers
                    )
                }
                to_create = []
                to_update = []
                for d in drivers:
                    rec = existing.get(d.D_ID)
                    if rec is None:
                        to_create.append(
                            driver_tool_box_meeting_attended(
                                meeting_attended_by=d,
                                meetings_attended=item_obj,
                                no_of_times_meeting_attended=1,
                            )
                        )
                    else:
                        rec.no_of_times_meeting_attended += 1
                        to_update.append(rec)
                if to_create:
                    driver_tool_box_meeting_attended.objects.bulk_create(to_create)
                if to_update:
                    driver_tool_box_meeting_attended.objects.bulk_update(
                        to_update, ["no_of_times_meeting_attended"]
                    )

        item_label = getattr(item_obj, config["item_label_field"])
        messages.success(
            request,
            f"Marked \"{item_label}\" for {len(drivers)} driver(s).",
        )
        return redirect(reverse("get_drivers"))

    drivers = Driver.objects.all().order_by("D_Name")
    context = {
        "kind": kind,
        "kind_label": config["label"],
        "item": item_obj,
        "item_label": getattr(item_obj, config["item_label_field"]),
        "completed_date": completed_date,
        "drivers": drivers,
    }
    return render(request, "training/bulk_mark_drivers.html", context)
