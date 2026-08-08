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
    HttpResponseRedirect,
)


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
