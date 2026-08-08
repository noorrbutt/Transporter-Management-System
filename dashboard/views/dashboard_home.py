import calendar
import json
from datetime import date, datetime

from ._shared import (
    Company,
    Driver,
    Procedure,
    Paginator,
    Vehicle,
    driver_tool_box_meeting_attended,
    messages,
    render,
    tool_box_meeting_topics,
)


def get_date_status(date, field_name):
    current_date = datetime.now().date()
    days_remaining = (date - current_date).days
    if days_remaining <= 0:
        return f"Expired"
    elif days_remaining <= 90:
        return f"Close to Expiry"
    else:
        return f"Valid"


def dashboard(request):
    total_vehicles = Vehicle.objects.filter(is_deleted=False).count()
    today = date.today()

    drivers = Driver.objects.filter(is_deleted=False)
    expired_cnic_list = drivers.filter(CNIC_Validity__lt=today).order_by("D_Name")
    expired_ddc_list = drivers.filter(DDC_Expiry_Date__lt=today).order_by("D_Name")
    expired_htv_license_list = drivers.filter(HTV_License_Expiry_Date__lt=today).order_by("D_Name")
    expired_general_list = drivers.filter(Expiry_Date__lt=today).order_by("D_Name")

    today = date.today()
    year = today.year
    month = today.month
    cal = calendar.monthcalendar(year, month)
    working_days = 0

    for week in cal:
        for day in week:
            if day != 0 and calendar.weekday(year, month, day) != 6:
                working_days += 1

    NON_DRIVER_STAFF_COUNT = 58
    total_manpower = NON_DRIVER_STAFF_COUNT + drivers.count()
    man_days_work = total_manpower * working_days
    meetings_data = (
        tool_box_meeting_topics.objects
        .prefetch_related("driver_tool_box_meeting_attended_set")
    )

    tbm_data = [
        meeting.driver_tool_box_meeting_attended_set.count()
        for meeting in meetings_data
    ]
    tbm_labels = [meeting.meeting_topic for meeting in meetings_data]

    context = {
        "total_drivers": drivers.count(),
        "total_vehicles": total_vehicles,
        "total_manpower": total_manpower,
        "man_days_work": man_days_work,
        "expired_cnic_list": expired_cnic_list,
        "expired_ddc_list": expired_ddc_list,
        "expired_htv_license_list": expired_htv_license_list,
        "expired_general_list": expired_general_list,
        "tbm_data": json.dumps(tbm_data),
        "tbm_labels": json.dumps(tbm_labels),
        "total_tbm_sessions": sum(tbm_data),
        "total_tbm_participants": driver_tool_box_meeting_attended.objects.count(),
    }
    return render(request, "dashboard.html", context)


home = dashboard


def get_procedures(request, category=None):
    procedures = Procedure.objects.all()
    if category:
        procedures = procedures.filter(category=category)
    return render(request, "static_content/procedures.html", {
        "procedures": procedures,
        "active_category": category,
    })


def get_dm(request):
    return get_procedures(request, category="dm")


def get_vm(request):
    return get_procedures(request, category="vm")


def get_hsep(request):
    return get_procedures(request, category="hse")


def get_op(request):
    return get_procedures(request, category="op")


def get_policies(request):
    return render(request, "static_content/policies.html")
