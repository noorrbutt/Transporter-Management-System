import json
from datetime import datetime
from io import BytesIO

from PIL import Image

from django.core.files.base import ContentFile

from ._shared import (
    Company,
    Driver,
    timezone,
    DriverDrillCompletion,
    DriverTrainingCompletion,
    Location,
    Paginator,
    get_object_or_404,
    logger,
    messages,
    redirect,
    render,
    superuser_required,
    transaction,
    HttpResponseRedirect,
    driver_tool_box_meeting_attended,
)
from dashboard.forms import DriverForm
from dashboard.services import compute_driver_expiry_statuses


@superuser_required
@transaction.atomic
def add_driver(request):
    omcc = Company.objects.all()
    locc = Location.objects.all()
    try:
        if request.method == "POST":
            form = DriverForm(request.POST, request.FILES)
            if form.is_valid():
                driver = form.save()
                return HttpResponseRedirect("/driverview/" + str(driver.D_ID) + "/")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect(request.path)
        else:
            context = {"omc": omcc, "loc": locc, "action": "Add"}
            return render(request, "driver/add_driver.html", context)
    except Exception as e:
        messages.error(request, f"Operation failed: {str(e)}")
        return redirect(request.path)


@superuser_required
@transaction.atomic
def edit_driver(request, driver_id):
    driver = get_object_or_404(Driver, D_ID=driver_id)
    omcc = Company.objects.all()
    locc = Location.objects.all()

    try:
        if request.method == "POST":
            form = DriverForm(request.POST, request.FILES)
            if form.is_valid():
                driver = form.save(instance=driver)
                if request.FILES.get("image"):
                    user_image = request.FILES.get("image")
                    if user_image:
                        allowed_ext = (".jpg", ".jpeg", ".png")
                        if not user_image.name.lower().endswith(allowed_ext):
                            messages.error(request, "Only JPG or PNG images are allowed.")
                            return redirect(request.path)
                        if user_image.size > 5 * 1024 * 1024:
                            messages.error(request, "Image must be smaller than 5MB.")
                            return redirect(request.path)
                        image = Image.open(user_image)
                        width, height = image.size
                        new_size = min(width, height)
                        left = (width - new_size) / 2
                        top = (height - new_size) / 2
                        right = (width + new_size) / 2
                        bottom = (height + new_size) / 2
                        image = image.crop((left, top, right, bottom))
                        image = image.resize((200, 200), Image.LANCZOS)
                        image_data = BytesIO()
                        image.save(image_data, format="JPEG")
                        driver.D_Image.save(user_image.name, ContentFile(image_data.getvalue()))
                return HttpResponseRedirect("/driverview/" + str(driver_id) + "/")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect(request.path)

        else:
            context = {"driver": driver, "omc": omcc, "loc": locc, "action": "Edit"}
            return render(request, "driver/add_driver.html", context)
    except Exception as e:
        logger.exception("Operation failed in %s", request.path)
        messages.error(
            request, "Something went wrong. Please check your input and try again."
        )
        return redirect(request.path)


@superuser_required
@transaction.atomic
def delete_driver(request, driver_id):
    if request.method != "POST":
        return redirect("/drivers")
    try:
        driver = get_object_or_404(Driver, D_ID=driver_id)
        driver.is_deleted = True
        driver.deleted_at = timezone.now()
        driver.deleted_by = request.user
        driver.save()
    except Exception:
        pass
    return redirect("/drivers")


def driver_view(request, driver_id):

    driver = get_object_or_404(Driver, D_ID=driver_id)
    training_completions = (
        DriverTrainingCompletion.objects.filter(driver=driver)
        .select_related("training")
        .order_by("training__id")
    )
    drill_completions = (
        DriverDrillCompletion.objects.filter(driver=driver)
        .select_related("drill")
        .order_by("drill__id")
    )

    for field_name, status_message in compute_driver_expiry_statuses(driver).items():
        setattr(driver, field_name, status_message)

    tbm = driver_tool_box_meeting_attended.objects.filter(
        meeting_attended_by=driver_id
    ).values_list("no_of_times_meeting_attended", flat=True)
    tbm_data = list(tbm)

    context = {
        "driver": driver,
        "tbm_data": json.dumps(tbm_data),
        "drill_completions": drill_completions,
        "training_completions": training_completions,
    }
    return render(request, "driver/driver_view.html", context)


def get_driver(request):

    drivers = (
        Driver.objects.select_related("Oil_Marketing_Company")
        .filter(is_deleted=False)
        .order_by("D_Name")
    )
    paginator = Paginator(drivers, 50)
    drivers = paginator.get_page(request.GET.get("page"))

    for driver in drivers:
        for field_name, status_message in compute_driver_expiry_statuses(driver).items():
            setattr(driver, field_name, status_message)

    context = {
        "drivers": drivers,
        "page_obj": drivers,
    }

    return render(request, "driver/driver.html", context)