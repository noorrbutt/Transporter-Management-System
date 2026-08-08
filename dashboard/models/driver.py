from datetime import date

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

from .company import Company


class Location(models.Model):
    LID = models.AutoField(primary_key=True, verbose_name="Location ID")
    Lname = models.CharField(max_length=255, verbose_name="Location Name")

    def __str__(self):
        return self.Lname

    class Meta:
        verbose_name_plural = "Locations"


class Driver(models.Model):
    D_ID = models.AutoField(primary_key=True, verbose_name="Driver ID")
    D_Number = models.CharField(max_length=20, verbose_name="Driver Number", null=True)
    Oil_Marketing_Company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        verbose_name="Oil Marketing Company",
        null=True,
    )
    D_Image = models.ImageField(
        max_length=500, null=True, blank=True, upload_to="driver_images/"
    )
    D_Name = models.CharField(max_length=255, verbose_name="Driver Name", null=True)
    Father_Name = models.CharField(
        max_length=255, verbose_name="Father Name", null=True
    )
    CNIC = models.CharField(max_length=13, null=True)
    CNIC_Validity = models.DateField(
        verbose_name="CNIC Validity Date", null=True, blank=True
    )
    Cell_Phone_Num = models.CharField(
        max_length=20, verbose_name="Cell Phone Number", null=True
    )
    DOB = models.DateField(verbose_name="Date of Birth", null=True, blank=True)

    DL_STATUS_CHOICES = [
        ("HTV", "HTV"),
        ("PSV", "PSV"),
        ("LTV", "LTV"),
    ]
    DL_Status = models.CharField(
        max_length=3,
        choices=DL_STATUS_CHOICES,
        verbose_name="Driving License Status",
        null=True,
    )
    Motorway_Trained = models.CharField(
        max_length=14, verbose_name="Motorway Trained", null=True
    )
    DDC_Issue_Date = models.DateField(
        verbose_name="Motorway Certification Issue Date", null=True, blank=True
    )
    Address = models.TextField(verbose_name="Address", null=True)
    License_No = models.CharField(
        max_length=20, verbose_name="License Number", null=True
    )
    HTV_License_Authority = models.ForeignKey(
        "Location",
        on_delete=models.CASCADE,
        verbose_name="HTV License Authority",
        null=True,
    )
    HTV_License_Issue_Date = models.DateField(
        verbose_name="HTV License Issue Date", null=True, blank=True
    )
    HTV_License_Expiry_Date = models.DateField(
        verbose_name="HTV License Expiry Date", null=True, blank=True
    )
    DDC_Expiry_Date = models.DateField(verbose_name="DDC Date", null=True, blank=True)
    Education = models.CharField(max_length=16, verbose_name="Education", null=True)
    Medical = models.BooleanField(verbose_name="Medical Status", null=True)
    Report_Date = models.DateField(
        null=True, blank=True, verbose_name="Medical Report Date"
    )
    Lab_Name = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Lab Name"
    )
    Expiry_Date = models.DateField(
        null=True, blank=True, verbose_name="Medical Expiry Date"
    )
    Blood_Group = models.CharField(
        max_length=10, verbose_name="Blood Group", null=True, blank=True
    )
    Medical_Health = models.CharField(
        max_length=5, verbose_name="Medical Health", null=True
    )
    Joining_Date = models.DateField(verbose_name="Joining Date", null=True, blank=True)
    Salary_Increment_Date = models.DateField(
        verbose_name="Salary Increment Date", null=True, blank=True
    )
    Experience = models.PositiveIntegerField(
        validators=[MinValueValidator(0)], verbose_name="Experience (years)", null=True
    )
    Leave_Date = models.DateField(null=True, blank=True, verbose_name="Leave Date")
    Leave_Resume = models.DateField(
        null=True, blank=True, verbose_name="Leave Resume Date"
    )
    Driving_Age = models.PositiveIntegerField(
        validators=[MinValueValidator(0)], verbose_name="Driving Age (years)", null=True
    )
    Previous_Company = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Previous Company"
    )
    Tank_Lorry = models.CharField(max_length=255, verbose_name="Tank Lorry", null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )

    @property
    def age(self):
        if not self.DOB:
            return None
        today = date.today()
        return (
            today.year
            - self.DOB.year
            - ((today.month, today.day) < (self.DOB.month, self.DOB.day))
        )

    def __str__(self):
        return self.D_Name

    class Meta:
        verbose_name_plural = "Drivers"
        constraints = [
            models.UniqueConstraint(
                fields=["CNIC"],
                condition=models.Q(is_deleted=False),
                name="uniq_driver_cnic_active",
            )
        ]
