from datetime import datetime


def get_date_status(date, field_name):
    current_date = datetime.now().date()
    days_remaining = (date - current_date).days
    if days_remaining <= 0:
        return "Expired"
    elif days_remaining <= 90:
        return "Close to Expiry"
    else:
        return "Valid"


def compute_driver_expiry_statuses(driver):
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

    statuses = {}
    for field_name, field_date in date_fields.items():
        if field_date:
            statuses[f"{field_name}_status"] = get_date_status(field_date, field_name)
    return statuses


def compute_vehicle_expiry_statuses(vehicle):
    date_fields = {
        "tax_expiry": vehicle.TAX_PAID_Date,
        "fitness_expiry": vehicle.FITNISSE_Date,
        "road_insurance": vehicle.INSURANCE_Date,
        "Dip_Chart": vehicle.DIP_CHART_Date,
        "Q_Fom": vehicle.Q_FOM_Date,
        "Route": vehicle.Route_Permit_Date,
    }

    statuses = {}
    for field_name, field_date in date_fields.items():
        if field_date:
            statuses[f"{field_name}_status"] = get_date_status(field_date, field_name)
    return statuses
