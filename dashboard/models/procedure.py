from django.db import models


class Procedure(models.Model):
    CATEGORY_CHOICES = [
        ("dm", "Driver Management"),
        ("vm", "Vehicle Management"),
        ("hse", "HSE"),
        ("op", "Operation Procedure"),
        ("general", "General"),

    ]
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    body = models.TextField()  # holds the inner HTML (the <ol>/<ul> list)
    order = models.PositiveIntegerField(default=0)  # to preserve display order

    class Meta:
        ordering = ["category", "order", "id"]

    def __str__(self):
        return f"{self.title} ({self.category})"