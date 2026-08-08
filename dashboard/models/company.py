from django.contrib.auth.models import User
from django.db import models


class Company(models.Model):
    cid = models.AutoField(primary_key=True, verbose_name="Company ID")
    cabb = models.CharField(max_length=10, verbose_name="Company Name abbreviation ")
    cname = models.CharField(max_length=255, verbose_name="Company Name")
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.cname

    class Meta:
        verbose_name_plural = "Companies"


class VehicleMaker(models.Model):
    VMid = models.AutoField(primary_key=True, verbose_name="Vehicle Maker ID")
    VMNAME = models.CharField(max_length=255, verbose_name="Vehicle Maker Name")
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.VMNAME

    class Meta:
        verbose_name_plural = "Vehicle Makers"


class VehicleOwner(models.Model):
    VO_id = models.AutoField(primary_key=True, verbose_name="Vehicle Owner ID")
    VO_name = models.CharField(max_length=255, verbose_name="Vehicle Owner Name")
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.VO_name

    class Meta:
        verbose_name_plural = "Vehicle Owners"
