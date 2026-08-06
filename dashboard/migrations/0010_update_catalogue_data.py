from django.db import migrations

NEW_VIOLATIONS = [
    "Black Spot",
    "Cell Phone",
    "Continuous Driving",
    "Duty Hours",
    "Night Drive",
    "PPE",
    "Route Diversion",
    "Seatbelt",
    "Smoking",
    "Speed",
]

NEW_DRILLS = [
    "BOMB THREAT",
    "BREAKDWON",
    "EMERGENCY RESPONSE (MAJOR DRILL)",
    "FIRE & EVACUATION",
    "FIRE FIGHTING",
    "FIRST AID",
    "HEART ATTACK",
    "HEAT STROKE",
    "PRODUCT SPILL",
    "ROAD ACCIDENT",
    "TIRE BURST",
    "LAW AND ORDER",
]

NEW_TRAININGS = [
    "ABS Break",
    "Company Policies",
    "Defensive Driving Revision",
    "Digital Driver Handbook",
    "Fatigue Management",
    "Journey Management",
    "Product Handling Knowledge",
    "Repair & Maintenance",
    "Reporting Stop Card, Near Miss and Incident",
    "Vehicle Inspection",
    "Vehicle Rollover Prevention",
]


def forwards(apps, schema_editor):
    Violations = apps.get_model("dashboard", "violations")
    AnnualDrill = apps.get_model("dashboard", "annual_drill")
    AnnualTraining = apps.get_model("dashboard", "annual_training")

    # Violations: drop anything not in the new list, add anything missing.
    Violations.objects.exclude(violation_type__in=NEW_VIOLATIONS).delete()
    existing = set(Violations.objects.values_list("violation_type", flat=True))
    for v in NEW_VIOLATIONS:
        if v not in existing:
            Violations.objects.create(violation_type=v)

    # Drills: same replace-by-name pattern, keeps rows still in use.
    AnnualDrill.objects.exclude(drill_name__in=NEW_DRILLS).delete()
    existing = set(AnnualDrill.objects.values_list("drill_name", flat=True))
    for d in NEW_DRILLS:
        if d not in existing:
            AnnualDrill.objects.create(drill_name=d, drilling_month="")

    # Trainings: same pattern.
    AnnualTraining.objects.exclude(train_name__in=NEW_TRAININGS).delete()
    existing = set(AnnualTraining.objects.values_list("train_name", flat=True))
    for t in NEW_TRAININGS:
        if t not in existing:
            AnnualTraining.objects.create(train_name=t, training_month="")


def backwards(apps, schema_editor):
    # Data-only migration; no reliable inverse. No-op keeps `migrate` reversible.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0009_alter_procedure_category"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
