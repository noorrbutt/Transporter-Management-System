from django import forms
from django.contrib.auth.models import User

from .models import Company, Driver, Location, Vehicle, VehicleMaker, VehicleOwner


class DriverForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id"] = forms.CharField(required=False)
        self.fields["name"] = forms.CharField(required=False)
        self.fields["father_name"] = forms.CharField(required=False)
        self.fields["cnic"] = forms.CharField(required=False)
        self.fields["cnic_date"] = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
        self.fields["cell"] = forms.CharField(required=False)
        self.fields["education"] = forms.CharField(required=False)
        self.fields["dob"] = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
        self.fields["address"] = forms.CharField(required=False)
        self.fields["driving_license_status"] = forms.CharField(required=False)
        self.fields["motorway_trained"] = forms.CharField(required=False)
        self.fields["motorway_certification_issue"] = forms.DateField(
            required=False, input_formats=["%Y-%m-%d"]
        )
        self.fields["license_no"] = forms.CharField(required=False)
        self.fields["htc_license"] = forms.CharField(required=False)
        self.fields["htv_license_issue"] = forms.DateField(
            required=False, input_formats=["%Y-%m-%d"]
        )
        self.fields["htv_license_expiry"] = forms.DateField(
            required=False, input_formats=["%Y-%m-%d"]
        )
        self.fields["Oil_Marketing_Company"] = forms.CharField(required=False)
        self.fields["medical_health"] = forms.CharField(required=False)
        self.fields["medical_issue"] = forms.DateField(
            required=False, input_formats=["%Y-%m-%d"]
        )
        self.fields["medical_expiry"] = forms.DateField(
            required=False, input_formats=["%Y-%m-%d"]
        )
        self.fields["lab"] = forms.CharField(required=False)
        self.fields["ddc_expiry"] = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
        self.fields["bg"] = forms.CharField(required=False)
        self.fields["joining"] = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
        self.fields["increment"] = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
        self.fields["leave"] = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
        self.fields["resume"] = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
        self.fields["driving_age"] = forms.CharField(required=False)
        self.fields["previous_company"] = forms.CharField(required=False)
        self.fields["tank_lorry"] = forms.CharField(required=False)
        self.fields["experience"] = forms.CharField(required=False)
        self.fields["image"] = forms.ImageField(required=False)

    def save(self, instance=None):
        data = self.cleaned_data
        driver = instance or Driver()
        driver.D_Number = data.get("id") or None
        driver.D_Name = data.get("name") or None
        driver.Father_Name = data.get("father_name") or None
        driver.CNIC = data.get("cnic") or None
        driver.CNIC_Validity = data.get("cnic_date") or None
        driver.Cell_Phone_Num = data.get("cell") or None
        driver.Education = data.get("education") or None
        driver.DOB = data.get("dob") or None
        driver.Address = data.get("address") or None
        driver.DL_Status = data.get("driving_license_status") or None
        driver.Motorway_Trained = data.get("motorway_trained") or None
        driver.DDC_Issue_Date = data.get("motorway_certification_issue") or None
        driver.License_No = data.get("license_no") or None
        driver.HTV_License_Issue_Date = data.get("htv_license_issue") or None
        driver.HTV_License_Expiry_Date = data.get("htv_license_expiry") or None
        driver.Medical_Health = data.get("medical_health") or None
        driver.Report_Date = data.get("medical_issue") or None
        driver.Lab_Name = data.get("lab") or None
        driver.DDC_Expiry_Date = data.get("ddc_expiry") or None
        driver.Blood_Group = data.get("bg") or None
        driver.Joining_Date = data.get("joining") or None
        driver.Salary_Increment_Date = data.get("increment") or None
        driver.Leave_Date = data.get("leave") or None
        driver.Leave_Resume = data.get("resume") or None
        driver.Driving_Age = data.get("driving_age") or None
        driver.Previous_Company = data.get("previous_company") or None
        driver.Tank_Lorry = data.get("tank_lorry") or None
        driver.Experience = data.get("experience") or None
        driver.Expiry_Date = data.get("medical_expiry") or None

        if data.get("Oil_Marketing_Company"):
            driver.Oil_Marketing_Company = Company.objects.get(
                cname=data["Oil_Marketing_Company"]
            )
        else:
            driver.Oil_Marketing_Company = None

        if data.get("htc_license"):
            driver.HTV_License_Authority = Location.objects.get(Lname=data["htc_license"])
        else:
            driver.HTV_License_Authority = None

        driver.save()
        return driver


class VehicleForm(forms.Form):
    tl_number = forms.CharField(required=False)
    capacity = forms.CharField(required=False)
    omc = forms.CharField(required=False)
    vmake = forms.CharField(required=False)
    chambers = forms.CharField(required=False)
    model = forms.CharField(required=False)
    engine_number = forms.CharField(required=False)
    chassis_number = forms.CharField(required=False)
    lease_company = forms.CharField(required=False)
    lease_bank = forms.CharField(required=False)
    status = forms.CharField(required=False)
    type = forms.CharField(required=False)
    trailer_id = forms.CharField(required=False)
    brand = forms.CharField(required=False)
    nha = forms.CharField(required=False)
    gross = forms.CharField(required=False)
    vd_ed = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
    vr_ed = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
    vt_ed = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
    vf_ed = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
    vq_ed = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
    vrp_ed = forms.DateField(required=False, input_formats=["%Y-%m-%d"])

    def save(self, instance=None):
        data = self.cleaned_data
        vehicle = instance or Vehicle()
        vehicle.TL_Number = data["tl_number"] or None
        vehicle.Capacity = data["capacity"] or None
        vehicle.Chambers = data["chambers"] or None
        vehicle.Model = data["model"] or None
        vehicle.Engine_Number = data["engine_number"] or None
        vehicle.Chassis_Number = data["chassis_number"] or None
        vehicle.Status = data["status"] or None
        vehicle.Type = data["type"] or None
        vehicle.Trailer_ID = data["trailer_id"] or None
        vehicle.Brand = data["brand"] or None
        vehicle.NHA_Configuration_Class = data["nha"] or None
        vehicle.Gross_Empty_Trailer_Weight = data["gross"] or None
        vehicle.DIP_CHART_Date = data["vd_ed"] or None
        vehicle.INSURANCE_Date = data["vr_ed"] or None
        vehicle.TAX_PAID_Date = data["vt_ed"] or None
        vehicle.FITNISSE_Date = data["vf_ed"] or None
        vehicle.Q_FOM_Date = data["vq_ed"] or None
        vehicle.Route_Permit_Date = data["vrp_ed"] or None

        if data.get("omc"):
            vehicle.OMC = Company.objects.get(cname=data["omc"])
        else:
            vehicle.OMC = None

        if data.get("vmake"):
            vehicle.Make = VehicleMaker.objects.get(VMNAME=data["vmake"])
        else:
            vehicle.Make = None

        if data.get("lease_company"):
            vehicle.LEASE_COMPANY = VehicleOwner.objects.get(VO_name=data["lease_company"])
        else:
            vehicle.LEASE_COMPANY = None

        if data.get("lease_bank"):
            vehicle.LEASE_BANK = VehicleOwner.objects.get(VO_name=data["lease_bank"])
        else:
            vehicle.LEASE_BANK = None

        vehicle.save()
        return vehicle


class CompanyForm(forms.Form):
    cabb = forms.CharField(max_length=10, required=False)
    company_name = forms.CharField(max_length=255, required=False)

    def save(self, instance=None):
        data = self.cleaned_data
        company = instance or Company()
        company.cabb = data["cabb"] or None
        company.cname = data["company_name"] or None
        company.save()
        return company


class UserForm(forms.Form):
    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        self.fields["first-name"] = forms.CharField(required=False)
        self.fields["last-name"] = forms.CharField(required=False)
        self.fields["username"] = forms.CharField(required=False)
        self.fields["password"] = forms.CharField(required=False, widget=forms.PasswordInput)
        self.fields["access-level"] = forms.CharField(required=False)
        self.fields["status"] = forms.CharField(required=False)
        self.fields["user_image"] = forms.ImageField(required=False)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not password and self.instance is None:
            raise forms.ValidationError("Password cannot be blank.")
        return password

    def save(self, instance=None):
        data = self.cleaned_data
        user = instance or User()
        user.username = data.get("username") or None
        user.first_name = data.get("first-name") or None
        user.last_name = data.get("last-name") or None
        if data.get("access-level") == "Full Access":
            user.is_superuser = True
        else:
            user.is_superuser = False
        if data.get("status") == "Active":
            user.is_active = True
        else:
            user.is_active = False

        if user.pk is None:
            user = User.objects.create_user(
                username=data.get("username"),
                password=data.get("password") or "",
            )
            user.first_name = data.get("first-name") or None
            user.last_name = data.get("last-name") or None
            user.is_superuser = True if data.get("access-level") == "Full Access" else False
            user.is_active = True if data.get("status") == "Active" else False
            user.save()
        else:
            if data.get("password"):
                user.set_password(data["password"])
            user.save()
        return user
