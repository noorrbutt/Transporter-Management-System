from django.db import models

from .driver import Driver


class annual_training(models.Model):
    id = models.AutoField(primary_key=True)
    train_name = models.CharField(max_length=255, verbose_name="Training Name")
    training_month = models.CharField(max_length=50, verbose_name="Training Month")

    def __str__(self):
        return self.train_name

    class Meta:
        verbose_name = "HSE Training"
        verbose_name_plural = "HSE Trainings"


class annual_drill(models.Model):
    id = models.AutoField(primary_key=True)
    drill_name = models.CharField(max_length=255, verbose_name="Drill Name")
    drilling_month = models.CharField(max_length=50, verbose_name="Dril Month")

    def __str__(self):
        return self.drill_name

    class Meta:
        verbose_name = "Drill Training"
        verbose_name_plural = "Drill Trainings"


class annual_drill_driver(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Driver, on_delete=models.CASCADE, verbose_name="User")
    train1_completed_date = models.DateField(null=True, blank=True)
    train2_completed_date = models.DateField(null=True, blank=True)
    train3_completed_date = models.DateField(null=True, blank=True)
    train4_completed_date = models.DateField(null=True, blank=True)
    train5_completed_date = models.DateField(null=True, blank=True)
    train6_completed_date = models.DateField(null=True, blank=True)
    train7_completed_date = models.DateField(null=True, blank=True)
    train8_completed_date = models.DateField(null=True, blank=True)
    train9_completed_date = models.DateField(null=True, blank=True)
    train10_completed_date = models.DateField(null=True, blank=True)
    train11_completed_date = models.DateField(null=True, blank=True)
    train12_completed_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Drill Driver"
        verbose_name_plural = "Drill Drivers"


class annual_training_driver(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Driver, on_delete=models.CASCADE, verbose_name="User")
    train1_completed_date = models.DateField(
        null=True, blank=True, verbose_name="TRAIN1 Completed Date"
    )
    train2_completed_date = models.DateField(
        null=True, blank=True, verbose_name="TRAIN2 Completed Date"
    )
    train3_completed_date = models.DateField(
        null=True, blank=True, verbose_name="TRAIN3 Completed Date"
    )
    train4_completed_date = models.DateField(
        null=True, blank=True, verbose_name="TRAIN4 Completed Date"
    )
    train5_completed_date = models.DateField(
        null=True, blank=True, verbose_name="TRAIN5 Completed Date"
    )
    train6_completed_date = models.DateField(
        null=True, blank=True, verbose_name="TRAIN6 Completed Date"
    )
    train7_completed_date = models.DateField(
        null=True, blank=True, verbose_name="TRAIN7 Completed Date"
    )
    train8_completed_date = models.DateField(
        null=True, blank=True, verbose_name="TRAIN8 Completed Date"
    )
    train9_completed_date = models.DateField(
        null=True, blank=True, verbose_name="TRAIN9 Completed Date"
    )
    train10_completed_date = models.DateField(
        null=True, blank=True, verbose_name="TRAIN10 Completed Date"
    )
    train11_completed_date = models.DateField(
        null=True, blank=True, verbose_name="TRAIN11 Completed Date"
    )
    train12_completed_date = models.DateField(
        null=True, blank=True, verbose_name="TRAIN12 Completed Date"
    )

    class Meta:
        verbose_name = "HSE Training Driver"
        verbose_name_plural = "HSE Training Drivers"


class DriverTrainingCompletion(models.Model):
    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, related_name="training_completions"
    )
    training = models.ForeignKey(
        annual_training, on_delete=models.CASCADE, related_name="driver_completions"
    )
    completed_date = models.DateField()

    class Meta:
        unique_together = ("driver", "training")
        verbose_name = "Driver Training Completion"
        verbose_name_plural = "Driver Training Completions"

    def __str__(self):
        return f"{self.driver} – {self.training} – {self.completed_date}"


class DriverDrillCompletion(models.Model):
    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, related_name="drill_completions"
    )
    drill = models.ForeignKey(
        annual_drill, on_delete=models.CASCADE, related_name="driver_completions"
    )
    completed_date = models.DateField()

    class Meta:
        unique_together = ("driver", "drill")
        verbose_name = "Driver Drill Completion"
        verbose_name_plural = "Driver Drill Completions"

    def __str__(self):
        return f"{self.driver} – {self.drill} – {self.completed_date}"


class tool_box_meeting_topics(models.Model):
    id = models.AutoField(primary_key=True)
    meeting_topic = models.CharField(
        max_length=255, verbose_name="Tool Box Meeting Topic"
    )

    def __str__(self):
        return self.meeting_topic

    class Meta:
        verbose_name = "Tool Box Meeting"
        verbose_name_plural = "Tool Box Meetings"


class driver_tool_box_meeting_attended(models.Model):
    id = models.AutoField(primary_key=True)
    meetings_attended = models.ForeignKey(
        tool_box_meeting_topics, on_delete=models.CASCADE, null=True
    )
    meeting_attended_by = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True)
    no_of_times_meeting_attended = models.IntegerField()
