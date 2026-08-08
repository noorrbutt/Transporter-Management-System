from ._shared import (
    Company,
    Http404,
    HttpResponseRedirect,
    Paginator,
    Vehicle,
    VehicleMaker,
    VehicleOwner,
    get_object_or_404,
    logger,
    messages,
    redirect,
    render,
    superuser_required,
    timezone,
    transaction,
)
from dashboard.forms import VehicleForm
from dashboard.services import compute_vehicle_expiry_statuses


@superuser_required
@transaction.atomic
def add_maker(request):
    try:
        if request.method == "POST":
            vehicle = VehicleMaker()
            vehicle.VMNAME = request.POST.get("maker")
            vehicle.save()
            return HttpResponseRedirect("/makers")
        else:
            return render(request, "vehicle_maker/add_vm.html", {"action": "Add"})
    except Exception as e:
        logger.exception("Operation failed in %s", request.path)
        messages.error(
            request, "Something went wrong. Please check your input and try again."
        )
        return redirect(request.path)


@superuser_required
@transaction.atomic
def edit_maker(request, maker_id):
    maker = get_object_or_404(VehicleMaker, VMid=maker_id)
    try:
        if request.method == "POST":
            maker.VMNAME = request.POST.get("maker")
            maker.save()
            return HttpResponseRedirect("/makers")
    except Exception as e:
        logger.exception("Operation failed in %s", request.path)
        messages.error(
            request, "Something went wrong. Please check your input and try again."
        )
        return redirect(request.path)
    return render(
        request, "vehicle_maker/add_vm.html", {"maker": maker, "action": "Edit"}
    )


@superuser_required
@transaction.atomic
def delete_maker(request, maker_id):
    if request.method != "POST":
        return HttpResponseRedirect("/makers")
    try:
        maker = get_object_or_404(VehicleMaker, VMid=maker_id)
        maker.is_deleted = True
        maker.deleted_at = timezone.now()
        maker.deleted_by = request.user
        maker.save()
        return HttpResponseRedirect("/makers")
    except Exception:
        return HttpResponseRedirect("/makers")


@superuser_required
@transaction.atomic
def add_owner(request):
    try:
        if request.method == "POST":
            owner = VehicleOwner()
            vowner = request.POST.get("vowner")
            owner.VO_name = vowner
            owner.save()
            return HttpResponseRedirect("/owners")
        else:
            return render(request, "vehicle_owner/add_vo.html", {"action": "Add"})
    except Exception as e:
        logger.exception("Operation failed in %s", request.path)
        messages.error(
            request, "Something went wrong. Please check your input and try again."
        )
        return redirect(request.path)


@superuser_required
@transaction.atomic
def edit_owner(request, owner_id):
    owner = get_object_or_404(VehicleOwner, VO_id=owner_id)
    try:
        if request.method == "POST":
            owner.VO_name = request.POST.get("vowner")
            owner.save()
            return HttpResponseRedirect("/owners")
    except Exception as e:
        logger.exception("Operation failed in %s", request.path)
        messages.error(
            request, "Something went wrong. Please check your input and try again."
        )
        return redirect(request.path)
    return render(
        request, "vehicle_owner/add_vo.html", {"owner": owner, "action": "Edit"}
    )


@superuser_required
@transaction.atomic
def delete_owner(request, owner_id):
    if request.method != "POST":
        return HttpResponseRedirect("/owners")
    try:
        owner = get_object_or_404(VehicleOwner, VO_id=owner_id)
        owner.is_deleted = True
        owner.deleted_at = timezone.now()
        owner.deleted_by = request.user
        owner.save()
        return HttpResponseRedirect("/owners")
    except Exception:
        return HttpResponseRedirect("/owners")


@superuser_required
@transaction.atomic
def add_vehicle(request):
    vehicle_makers = VehicleMaker.objects.all()
    vehicle_owners = VehicleOwner.objects.all()
    company = Company.objects.all()

    if request.method == "POST":
        try:
            form = VehicleForm(request.POST)
            if form.is_valid():
                new_vehicle = form.save()
                return HttpResponseRedirect("/vehicleview/" + str(new_vehicle.id) + "/")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect(request.path)
        except Exception as e:
            logger.exception("Operation failed in %s", request.path)
            messages.error(
                request, "Something went wrong. Please check your input and try again."
            )
            return redirect(request.path)

    context = {
        "vehicle_makers": vehicle_makers,
        "vehicle_owners": vehicle_owners,
        "company": company,
        "form_heading": "Add a new Vehicle",
        "action": "Add",
    }
    return render(request, "vehicle/add_vehicle.html", context)


@superuser_required
@transaction.atomic
def edit_vehicle(request, vehicle_id):
    vehicle_makers = VehicleMaker.objects.all()
    vehicle_owners = VehicleOwner.objects.all()
    company = Company.objects.all()

    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)

    if request.method == "POST":
        try:
            form = VehicleForm(request.POST)
            if form.is_valid():
                form.save(instance=vehicle)
                return HttpResponseRedirect("/vehicleview/" + str(vehicle.id) + "/")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect(request.path)
        except Exception as e:
            logger.exception("Operation failed in %s", request.path)
            messages.error(
                request, "Something went wrong. Please check your input and try again."
            )
            return redirect(request.path)

    context = {
        "vehicle_makers": vehicle_makers,
        "vehicle_owners": vehicle_owners,
        "vehicle": vehicle,
        "company": company,
        "form_heading": "Edit Vehicle Details",
        "action": "Edit",
    }
    return render(request, "vehicle/add_vehicle.html", context)


@superuser_required
@transaction.atomic
def delete_vehicle(request, vehicle_id):
    if request.method != "POST":
        return redirect("/vehicles/all/")
    try:
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
        vehicle.is_deleted = True
        vehicle.deleted_at = timezone.now()
        vehicle.deleted_by = request.user
        vehicle.save()
    except Exception:
        pass
    return redirect("/vehicles/all/")


def vehicle_view(request, vehicle_id):

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    for field_name, status_message in compute_vehicle_expiry_statuses(vehicle).items():
        setattr(vehicle, field_name, status_message)

    context = {"vehicle": vehicle}
    return render(request, "vehicle/vehicleview.html", context)


def get_vehicle(request, filter):

    if filter == "apl":
        apl_company = Company.objects.filter(cabb__iexact="APL").first()
        vehicles = (
            Vehicle.objects.filter(OMC=apl_company, is_deleted=False)
            if apl_company
            else Vehicle.objects.none()
        )
        image = "/static/images/attock-logo.png"
    elif filter == "pso":
        pso_company = Company.objects.filter(cabb__iexact="PSO").first()
        vehicles = (
            Vehicle.objects.filter(OMC=pso_company, is_deleted=False)
            if pso_company
            else Vehicle.objects.none()
        )
        image = "/static/images/pso-logo.png"
    elif filter == "go":
        go_company = Company.objects.filter(cabb__iexact="GO").first()
        vehicles = (
            Vehicle.objects.filter(OMC=go_company, is_deleted=False)
            if go_company
            else Vehicle.objects.none()
        )
        image = "/static/images/go-logo.png"
    elif filter == "tppl":
        tppl_companies = Company.objects.filter(cabb__iexact="TPPL")
        vehicles = (
            Vehicle.objects.filter(OMC__in=tppl_companies, is_deleted=False)
            if tppl_companies.exists()
            else Vehicle.objects.none()
        )
        image = "/static/images/total-logo.png"
    elif filter == "all":
        vehicles = Vehicle.objects.filter(is_deleted=False)
        image = ""
    else:
        raise Http404("Unknown vehicle filter")

    paginator = Paginator(vehicles, 50)
    vehicles = paginator.get_page(request.GET.get("page"))

    for vehicle in vehicles:
        for field_name, status_message in compute_vehicle_expiry_statuses(vehicle).items():
            setattr(vehicle, field_name, status_message)

    context = {"vehicles": vehicles, "page_obj": vehicles, "image": image}
    return render(request, "vehicle/vehicle.html", context)


def get_vehicle_maker(request):

    vehicle_makers = VehicleMaker.objects.filter(is_deleted=False)
    context = {"vehicle_makers": vehicle_makers}
    return render(request, "vehicle_maker/vehicle_makers.html", context)


def get_vehicle_owner(request):

    vehicle_owners = VehicleOwner.objects.filter(is_deleted=False)
    context = {"vehicle_owners": vehicle_owners}
    return render(request, "vehicle_owner/vehicle_owner.html", context)
