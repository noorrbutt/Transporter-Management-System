from django.db import models

from .driver import Driver


class Violations(models.Model):
    id = models.AutoField(primary_key=True)
    violation_type = models.CharField(max_length=255, verbose_name="Violation Type")

    def __str__(self):
        return self.violation_type

    class Meta:
        verbose_name = "Violation"
        verbose_name_plural = "Violations"


class Driver_Violation(models.Model):
    id = models.AutoField(primary_key=True)
    violation = models.ForeignKey(
        Violations, on_delete=models.CASCADE, verbose_name="Violation", null=True
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, verbose_name="Driver", null=True
    )
    violation_date = models.DateField(verbose_name="Violation Date", null=True)
    violation_notes = models.TextField(null=True)

    def __str__(self):
        return f"{self.driver} - {self.violation} - {self.violation_date}"

    class Meta:
        verbose_name = "Driver Violation"
        verbose_name_plural = "Driver Violations"
