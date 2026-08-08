from django.contrib.auth.models import User
from django.db import models

from .company import Company, VehicleMaker, VehicleOwner


class Vehicle(models.Model):
    id = models.AutoField(primary_key=True)
    TL_Number = models.CharField(max_length=255, null=True)
    Capacity = models.IntegerField(null=True)
    Chambers = models.CharField(max_length=255, null=True)
    OMC = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)
    Make = models.ForeignKey(VehicleMaker, on_delete=models.CASCADE, null=True)
    Model = models.IntegerField(null=True)
    Engine_Number = models.CharField(max_length=255, null=True)
    Chassis_Number = models.CharField(max_length=255, null=True)
    LEASE_COMPANY = models.ForeignKey(
        VehicleOwner,
        on_delete=models.CASCADE,
        null=True,
        related_name="Vehicle_Owner_Lease",
    )
    LEASE_BANK = models.ForeignKey(
        VehicleOwner,
        on_delete=models.CASCADE,
        null=True,
        related_name="Vehicle_Owner_Bank",
    )
    Status = models.CharField(max_length=255, null=True)
    Type = models.CharField(max_length=255, null=True)
    Trailer_ID = models.CharField(max_length=255, null=True)
    Brand = models.CharField(max_length=255, null=True)
    NHA_Configuration_Class = models.CharField(max_length=255, null=True)
    Gross_Empty_Trailer_Weight = models.CharField(max_length=255, null=True)
    DIP_CHART_Date = models.DateField(null=True)
    INSURANCE_Date = models.DateField(null=True)
    TAX_PAID_Date = models.DateField(null=True)
    FITNISSE_Date = models.DateField(null=True)
    Q_FOM_Date = models.DateField(null=True)
    Route_Permit_Date = models.DateField(null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return str(self.TL_Number)

    class Meta:
        verbose_name_plural = "Vehicles"
        constraints = [
            models.UniqueConstraint(
                fields=["TL_Number"],
                condition=models.Q(is_deleted=False),
                name="uniq_vehicle_tlnumber_active",
            )
        ]
