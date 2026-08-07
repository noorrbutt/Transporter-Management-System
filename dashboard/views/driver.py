import json
from datetime import datetime
from io import BytesIO

from PIL import Image

from ._shared import (
    Company,
    ContentFile,
    Driver,
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
)
from .dashboard_home import get_date_status


@superuser_required
@transaction.atomic
def add_driver(request):
    omcc = Company.objects.all()
    locc = Location.objects.all()
    try:
        if request.method == "POST":
            id = request.POST.get("id")
            user_image = request.FILES.get("image")
            name = request.POST.get("name")
            father_name = request.POST.get("father_name")
            cnic = request.POST.get("cnic")
            cnic_date = request.POST.get("cnic_date")
            cell = request.POST.get("cell")
            education = request.POST.get("education")
            dob = request.POST.get("dob")
            address = request.POST.get("address")
            driving_license_status = request.POST.get("driving_license_status")
            motorway_trained = request.POST.get("motorway_trained")
            motorway_certification_issue = request.POST.get(
                "motorway_certification_issue"
            )
            license_no = request.POST.get("license_no")
            htc_license = request.POST.get("htc_license")
            htv_license_issue = request.POST.get("htv_license_issue")
            htv_license_expiry = request.POST.get("htv_license_expiry")
            oil_market = request.POST.get("Oil_Marketing_Company")
            medical_health = request.POST.get("medical_health")
            medical_issue = request.POST.get("medical_issue")
            medical_expiry = request.POST.get("medical_expiry")
            lab = request.POST.get("lab")
            ddc_expiry = request.POST.get("ddc_expiry")
            bg = request.POST.get("bg")
            joining = request.POST.get("joining")
            increment = request.POST.get("increment")
            leave = request.POST.get("leave")
            resume = request.POST.get("resume")
            driving_age = request.POST.get("experience")
            previous_company = request.POST.get("previous_company")
            tank_lorry = request.POST.get("tank_lorry")
            experience = request.POST.get("experience")
            omc_obj = Company.objects.get(cname=oil_market)
            htv_obj = Location.objects.get(Lname=htc_license)
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
                image_name = user_image.name
                image_data.seek(0)
                image_file = ContentFile(image_data.getvalue(), name=user_image.name)
            else:
                image_data = None
                image_file = None
            driver = Driver(
                D_Number=id,
                D_Image=image_file,
                D_Name=name,
                Father_Name=father_name,
                CNIC=cnic,
                CNIC_Validity=cnic_date if cnic_date else None,
                Cell_Phone_Num=cell,
                Education=education,
                DOB=datetime.strptime(dob, "%Y-%m-%d") if dob else None,
                Address=address,
                DL_Status=driving_license_status if driving_license_status else None,
                Motorway_Trained=motorway_trained if motorway_trained else None,
                DDC_Issue_Date=(
                    motorway_certification_issue
                    if motorway_certification_issue
                    else None
                ),
                License_No=license_no if license_no else None,
                HTV_License_Authority=htv_obj,
                HTV_License_Issue_Date=htv_license_issue if htv_license_issue else None,
                HTV_License_Expiry_Date=(
                    htv_license_expiry if htv_license_expiry else None
                ),
                Oil_Marketing_Company=omc_obj,
                Medical_Health=medical_health if medical_health else None,
                Report_Date=medical_issue if medical_issue else None,
                Lab_Name=lab if lab else None,
                DDC_Expiry_Date=ddc_expiry if ddc_expiry else None,
                Blood_Group=bg if bg else None,
                Joining_Date=joining if joining else None,
                Salary_Increment_Date=increment if increment else None,
                Leave_Date=leave if leave else None,
                Leave_Resume=resume if resume else None,
                Driving_Age=driving_age if driving_age else None,
                Previous_Company=previous_company if previous_company else None,
                Tank_Lorry=tank_lorry if tank_lorry else None,
                Experience=experience if experience else None,
                Expiry_Date=medical_expiry if medical_expiry else None,
            )
            driver.save()
            return HttpResponseRedirect("/driverview/" + str(driver.D_ID) + "/")
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
            id = request.POST.get("id")
            user_image = request.FILES.get("image")
            name = request.POST.get("name")
            father_name = request.POST.get("father_name")
            cnic = request.POST.get("cnic")
            cnic_date = request.POST.get("cnic_date")
            cell = request.POST.get("cell")
            education = request.POST.get("education")
            dob = request.POST.get("dob")
            address = request.POST.get("address")
            driving_license_status = request.POST.get("driving_license_status")
            motorway_trained = request.POST.get("motorway_trained")
            motorway_certification_issue = request.POST.get(
                "motorway_certification_issue"
            )
            license_no = request.POST.get("license_no")
            htc_license = request.POST.get("htc_license")
            htv_license_issue = request.POST.get("htv_license_issue")
            htv_license_expiry = request.POST.get("htv_license_expiry")
            oil_market = request.POST.get("Oil_Marketing_Company")
            medical_health = request.POST.get("medical_health")
            medical_issue = request.POST.get("medical_issue")
            medical_expiry = request.POST.get("medical_expiry")
            lab = request.POST.get("lab")
            ddc_expiry = request.POST.get("ddc_expiry")
            bg = request.POST.get("bg")
            joining = request.POST.get("joining")
            increment = request.POST.get("increment")
            leave = request.POST.get("leave")
            resume = request.POST.get("resume")
            driving_age = request.POST.get("experience")
            previous_company = request.POST.get("previous_company")
            tank_lorry = request.POST.get("tank_lorry")
            experience = request.POST.get("experience")

            omc_obj = Company.objects.get(cname=oil_market)
            htv_obj = Location.objects.get(Lname=htc_license)

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

            driver.D_Number = id
            driver.D_Name = name
            driver.Father_Name = father_name
            driver.CNIC = cnic
            driver.CNIC_Validity = cnic_date if cnic_date else None
            driver.Cell_Phone_Num = cell
            driver.Education = education
            driver.DOB = datetime.strptime(dob, "%Y-%m-%d") if dob else None
            driver.Address = address
            driver.DL_Status = (
                driving_license_status if driving_license_status else None
            )
            driver.Motorway_Trained = motorway_trained if motorway_trained else None
            driver.DDC_Issue_Date = (
                motorway_certification_issue if motorway_certification_issue else None
            )
            driver.License_No = license_no if license_no else None
            driver.HTV_License_Authority = htv_obj
            driver.HTV_License_Issue_Date = (
                htv_license_issue if htv_license_issue else None
            )
            driver.HTV_License_Expiry_Date = (
                htv_license_expiry if htv_license_expiry else None
            )
            driver.Oil_Marketing_Company = omc_obj
            driver.Medical_Health = medical_health if medical_health else None
            driver.Report_Date = medical_issue if medical_issue else None
            driver.Lab_Name = lab if lab else None
            driver.DDC_Expiry_Date = ddc_expiry if ddc_expiry else None
            driver.Blood_Group = bg if bg else None
            driver.Joining_Date = joining if joining else None
            driver.Salary_Increment_Date = increment if increment else None
            driver.Leave_Date = leave if leave else None
            driver.Leave_Resume = resume if resume else None
            driver.Driving_Age = driving_age if driving_age else None
            driver.Previous_Company = previous_company if previous_company else None
            driver.Tank_Lorry = tank_lorry if tank_lorry else None
            driver.Experience = experience if experience else None
            driver.Expiry_Date = medical_expiry if medical_expiry else None
            driver.save()

            return HttpResponseRedirect("/driverview/" + str(driver_id) + "/")

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
    date_fields = {
        "CNIC_Validity": driver.CNIC_Validity,
        "Motorway_Cissue_Date": driver.DDC_Issue_Date,
        "HTV_License_Issue_Date": driver.HTV_License_Issue_Date,
        "HTV_License_Expiry_Date": driver.HTV_License_Expiry_Date,
        "DDC_Date": driver.DDC_Expiry_Date,
        "Report_Date": driver.Report_Date,
        "Expiry_Date": driver.Expiry_Date,
        "Joining_Date": driver.Joining_Date,
        "Salary_Increment_Date": driver.Salary_Increment_Date,
        "Leave_Date": driver.Leave_Date,
        "Leave_Resume": driver.Leave_Resume,
    }
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

    for field_name, field_date in date_fields.items():
        if field_date:
            status_message = get_date_status(field_date, field_name)
            setattr(driver, f"{field_name}_status", status_message)

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
        date_fields = {
            "CNIC_Validity": driver.CNIC_Validity,
            "Motorway_Cissue_Date": driver.DDC_Issue_Date,
            "HTV_License_Issue_Date": driver.HTV_License_Issue_Date,
            "HTV_License_Expiry_Date": driver.HTV_License_Expiry_Date,
            "DDC_Date": driver.DDC_Expiry_Date,
            "Report_Date": driver.Report_Date,
            "Expiry_Date": driver.Expiry_Date,
            "Joining_Date": driver.Joining_Date,
            "Salary_Increment_Date": driver.Salary_Increment_Date,
            "Leave_Date": driver.Leave_Date,
            "Leave_Resume": driver.Leave_Resume,
        }

        for field_name, field_date in date_fields.items():
            if field_date:
                status_message = get_date_status(field_date, field_name)
                setattr(driver, f"{field_name}_status", status_message)

    context = {
        "drivers": drivers,
        "page_obj": drivers,
    }

    return render(request, "driver/driver.html", context)
