"""
Generic CSV import / export engine for the dashboard app.

This mirrors the "field-mapping" CSV import pattern (upload -> map CSV
columns to model fields -> preview/confirm -> import) and the
column-selectable CSV export pattern, adapted to a single-tenant,
synchronous Django app (no session/task-queue infrastructure needed).

Two entities are configured out of the box: Driver and Vehicle.
Adding a third entity later only means adding one more `*_FIELDS` /
`*_EXPORT_COLUMNS` pair below and two thin view functions.
"""
import csv
import io
import logging
import re
from datetime import datetime

from django.db import IntegrityError

from .models import Company, Driver, Location, Vehicle, VehicleMaker, VehicleOwner

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%Y/%m/%d",
)

TRUE_VALUES = {"yes", "y", "true", "1", "pass", "passed", "ok"}
FALSE_VALUES = {"no", "n", "false", "0", "fail", "failed"}


def _normalize(text):
    """Lowercase, alnum-only key used to fuzzy-match a CSV header to a field label/key."""
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def parse_csv_date(value):
    value = (value or "").strip()
    if not value:
        return None, None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date(), None
        except ValueError:
            continue
    return None, f"Unrecognised date '{value}'"


def parse_csv_int(value):
    value = (value or "").strip()
    if not value:
        return None, None
    try:
        return int(float(value)), None
    except ValueError:
        return None, f"Unrecognised number '{value}'"


def parse_csv_bool(value):
    value = (value or "").strip().lower()
    if not value:
        return None, None
    if value in TRUE_VALUES:
        return True, None
    if value in FALSE_VALUES:
        return False, None
    return None, f"Unrecognised yes/no value '{value}'"


def resolve_fk(model, match_field, value, cache):
    """Get-or-create a related object by its display field, memoised per import run."""
    value = (value or "").strip()
    if not value:
        return None, None
    cache_key = (model, value.lower())
    if cache_key in cache:
        return cache[cache_key], None
    obj = model.objects.filter(**{f"{match_field}__iexact": value}).first()
    if not obj:
        obj = model.objects.create(**{match_field: value})
    cache[cache_key] = obj
    return obj, None


# ---------------------------------------------------------------------------
# Field registries — (key, label, kind, extra) per importable model field.
# kind in: text, int, date, bool, choice, fk
# ---------------------------------------------------------------------------

DRIVER_FIELDS = [
    {"key": "D_Name", "label": "Driver Name", "kind": "text", "required": True},
    {"key": "D_Number", "label": "Driver Number", "kind": "text"},
    {"key": "Oil_Marketing_Company", "label": "Oil Marketing Company", "kind": "fk",
     "fk_model": Company, "fk_field": "cname"},
    {"key": "Father_Name", "label": "Father Name", "kind": "text"},
    {"key": "CNIC", "label": "CNIC", "kind": "text"},
    {"key": "CNIC_Validity", "label": "CNIC Validity Date", "kind": "date"},
    {"key": "Cell_Phone_Num", "label": "Cell Phone Number", "kind": "text"},
    {"key": "DOB", "label": "Date of Birth", "kind": "date"},
    {"key": "DL_Status", "label": "Driving License Status", "kind": "choice",
     "choices": ["HTV", "PSV", "LTV"]},
    {"key": "Motorway_Trained", "label": "Motorway Trained", "kind": "text"},
    {"key": "DDC_Issue_Date", "label": "Motorway Certification Issue Date", "kind": "date"},
    {"key": "Address", "label": "Address", "kind": "text"},
    {"key": "License_No", "label": "License Number", "kind": "text"},
    {"key": "HTV_License_Authority", "label": "HTV License Authority", "kind": "fk",
     "fk_model": Location, "fk_field": "Lname"},
    {"key": "HTV_License_Issue_Date", "label": "HTV License Issue Date", "kind": "date"},
    {"key": "HTV_License_Expiry_Date", "label": "HTV License Expiry Date", "kind": "date"},
    {"key": "DDC_Expiry_Date", "label": "DDC Date", "kind": "date"},
    {"key": "Education", "label": "Education", "kind": "text"},
    {"key": "Medical", "label": "Medical Status", "kind": "bool"},
    {"key": "Report_Date", "label": "Medical Report Date", "kind": "date"},
    {"key": "Lab_Name", "label": "Lab Name", "kind": "text"},
    {"key": "Expiry_Date", "label": "Medical Expiry Date", "kind": "date"},
    {"key": "Blood_Group", "label": "Blood Group", "kind": "text"},
    {"key": "Medical_Health", "label": "Medical Health", "kind": "text"},
    {"key": "Joining_Date", "label": "Joining Date", "kind": "date"},
    {"key": "Salary_Increment_Date", "label": "Salary Increment Date", "kind": "date"},
    {"key": "Experience", "label": "Experience (years)", "kind": "int"},
    {"key": "Leave_Date", "label": "Leave Date", "kind": "date"},
    {"key": "Leave_Resume", "label": "Leave Resume Date", "kind": "date"},
    {"key": "Driving_Age", "label": "Driving Age (years)", "kind": "int"},
    {"key": "Previous_Company", "label": "Previous Company", "kind": "text"},
    {"key": "Tank_Lorry", "label": "Tank Lorry", "kind": "text"},
]

VEHICLE_FIELDS = [
    {"key": "TL_Number", "label": "TL Number", "kind": "text", "required": True},
    {"key": "Capacity", "label": "Capacity", "kind": "int"},
    {"key": "Chambers", "label": "Chambers", "kind": "text"},
    {"key": "OMC", "label": "Oil Marketing Company", "kind": "fk",
     "fk_model": Company, "fk_field": "cname"},
    {"key": "Make", "label": "Vehicle Maker", "kind": "fk",
     "fk_model": VehicleMaker, "fk_field": "VMNAME"},
    {"key": "Model", "label": "Model Year", "kind": "int"},
    {"key": "Engine_Number", "label": "Engine Number", "kind": "text"},
    {"key": "Chassis_Number", "label": "Chassis Number", "kind": "text"},
    {"key": "LEASE_COMPANY", "label": "Lease Company", "kind": "fk",
     "fk_model": VehicleOwner, "fk_field": "VO_name"},
    {"key": "LEASE_BANK", "label": "Lease Bank", "kind": "fk",
     "fk_model": VehicleOwner, "fk_field": "VO_name"},
    {"key": "Status", "label": "Status", "kind": "text"},
    {"key": "Type", "label": "Type", "kind": "text"},
    {"key": "Trailer_ID", "label": "Trailer ID", "kind": "text"},
    {"key": "Brand", "label": "Brand", "kind": "text"},
    {"key": "NHA_Configuration_Class", "label": "NHA Configuration Class", "kind": "text"},
    {"key": "Gross_Empty_Trailer_Weight", "label": "Gross Empty Trailer Weight", "kind": "text"},
    {"key": "DIP_CHART_Date", "label": "Dip Chart Date", "kind": "date"},
    {"key": "INSURANCE_Date", "label": "Insurance Date", "kind": "date"},
    {"key": "TAX_PAID_Date", "label": "Tax Paid Date", "kind": "date"},
    {"key": "FITNISSE_Date", "label": "Fitness Date", "kind": "date"},
    {"key": "Q_FOM_Date", "label": "Q FOM Date", "kind": "date"},
    {"key": "Route_Permit_Date", "label": "Route Permit Date", "kind": "date"},
]


def _fk_display(obj, field):
    return getattr(obj, field, "") or "" if obj else ""


DRIVER_EXPORT_COLUMNS = [
    ("D_Number", "Driver Number", lambda d: d.D_Number or ""),
    ("D_Name", "Driver Name", lambda d: d.D_Name or ""),
    ("Father_Name", "Father Name", lambda d: d.Father_Name or ""),
    ("Oil_Marketing_Company", "Oil Marketing Company", lambda d: _fk_display(d.Oil_Marketing_Company, "cname")),
    ("CNIC", "CNIC", lambda d: d.CNIC or ""),
    ("CNIC_Validity", "CNIC Validity Date", lambda d: d.CNIC_Validity.isoformat() if d.CNIC_Validity else ""),
    ("Cell_Phone_Num", "Cell Phone Number", lambda d: d.Cell_Phone_Num or ""),
    ("DOB", "Date of Birth", lambda d: d.DOB.isoformat() if d.DOB else ""),
    ("DL_Status", "Driving License Status", lambda d: d.DL_Status or ""),
    ("Motorway_Trained", "Motorway Trained", lambda d: d.Motorway_Trained or ""),
    ("DDC_Issue_Date", "Motorway Certification Issue Date", lambda d: d.DDC_Issue_Date.isoformat() if d.DDC_Issue_Date else ""),
    ("Address", "Address", lambda d: d.Address or ""),
    ("License_No", "License Number", lambda d: d.License_No or ""),
    ("HTV_License_Authority", "HTV License Authority", lambda d: _fk_display(d.HTV_License_Authority, "Lname")),
    ("HTV_License_Issue_Date", "HTV License Issue Date", lambda d: d.HTV_License_Issue_Date.isoformat() if d.HTV_License_Issue_Date else ""),
    ("HTV_License_Expiry_Date", "HTV License Expiry Date", lambda d: d.HTV_License_Expiry_Date.isoformat() if d.HTV_License_Expiry_Date else ""),
    ("DDC_Expiry_Date", "DDC Date", lambda d: d.DDC_Expiry_Date.isoformat() if d.DDC_Expiry_Date else ""),
    ("Education", "Education", lambda d: d.Education or ""),
    ("Medical", "Medical Status", lambda d: "Yes" if d.Medical else ("No" if d.Medical is False else "")),
    ("Report_Date", "Medical Report Date", lambda d: d.Report_Date.isoformat() if d.Report_Date else ""),
    ("Lab_Name", "Lab Name", lambda d: d.Lab_Name or ""),
    ("Expiry_Date", "Medical Expiry Date", lambda d: d.Expiry_Date.isoformat() if d.Expiry_Date else ""),
    ("Blood_Group", "Blood Group", lambda d: d.Blood_Group or ""),
    ("Medical_Health", "Medical Health", lambda d: d.Medical_Health or ""),
    ("Joining_Date", "Joining Date", lambda d: d.Joining_Date.isoformat() if d.Joining_Date else ""),
    ("Salary_Increment_Date", "Salary Increment Date", lambda d: d.Salary_Increment_Date.isoformat() if d.Salary_Increment_Date else ""),
    ("Experience", "Experience (years)", lambda d: d.Experience if d.Experience is not None else ""),
    ("Leave_Date", "Leave Date", lambda d: d.Leave_Date.isoformat() if d.Leave_Date else ""),
    ("Leave_Resume", "Leave Resume Date", lambda d: d.Leave_Resume.isoformat() if d.Leave_Resume else ""),
    ("Driving_Age", "Driving Age (years)", lambda d: d.Driving_Age if d.Driving_Age is not None else ""),
    ("Previous_Company", "Previous Company", lambda d: d.Previous_Company or ""),
    ("Tank_Lorry", "Tank Lorry", lambda d: d.Tank_Lorry or ""),
]

VEHICLE_EXPORT_COLUMNS = [
    ("TL_Number", "TL Number", lambda v: v.TL_Number or ""),
    ("Capacity", "Capacity", lambda v: v.Capacity if v.Capacity is not None else ""),
    ("Chambers", "Chambers", lambda v: v.Chambers or ""),
    ("OMC", "Oil Marketing Company", lambda v: _fk_display(v.OMC, "cname")),
    ("Make", "Vehicle Maker", lambda v: _fk_display(v.Make, "VMNAME")),
    ("Model", "Model Year", lambda v: v.Model if v.Model is not None else ""),
    ("Engine_Number", "Engine Number", lambda v: v.Engine_Number or ""),
    ("Chassis_Number", "Chassis Number", lambda v: v.Chassis_Number or ""),
    ("LEASE_COMPANY", "Lease Company", lambda v: _fk_display(v.LEASE_COMPANY, "VO_name")),
    ("LEASE_BANK", "Lease Bank", lambda v: _fk_display(v.LEASE_BANK, "VO_name")),
    ("Status", "Status", lambda v: v.Status or ""),
    ("Type", "Type", lambda v: v.Type or ""),
    ("Trailer_ID", "Trailer ID", lambda v: v.Trailer_ID or ""),
    ("Brand", "Brand", lambda v: v.Brand or ""),
    ("NHA_Configuration_Class", "NHA Configuration Class", lambda v: v.NHA_Configuration_Class or ""),
    ("Gross_Empty_Trailer_Weight", "Gross Empty Trailer Weight", lambda v: v.Gross_Empty_Trailer_Weight or ""),
    ("DIP_CHART_Date", "Dip Chart Date", lambda v: v.DIP_CHART_Date.isoformat() if v.DIP_CHART_Date else ""),
    ("INSURANCE_Date", "Insurance Date", lambda v: v.INSURANCE_Date.isoformat() if v.INSURANCE_Date else ""),
    ("TAX_PAID_Date", "Tax Paid Date", lambda v: v.TAX_PAID_Date.isoformat() if v.TAX_PAID_Date else ""),
    ("FITNISSE_Date", "Fitness Date", lambda v: v.FITNISSE_Date.isoformat() if v.FITNISSE_Date else ""),
    ("Q_FOM_Date", "Q FOM Date", lambda v: v.Q_FOM_Date.isoformat() if v.Q_FOM_Date else ""),
    ("Route_Permit_Date", "Route Permit Date", lambda v: v.Route_Permit_Date.isoformat() if v.Route_Permit_Date else ""),
]


# Registry of importable/exportable entities, keyed by a URL-friendly slug.
ENTITIES = {
    "driver": {
        "model": Driver,
        "fields": DRIVER_FIELDS,
        "export_columns": DRIVER_EXPORT_COLUMNS,
        "natural_key": "D_Number",
        "list_url": "get_drivers",
        "label": "Driver",
        "label_plural": "Drivers",
    },
    "vehicle": {
        "model": Vehicle,
        "fields": VEHICLE_FIELDS,
        "export_columns": VEHICLE_EXPORT_COLUMNS,
        "natural_key": "TL_Number",
        "list_url": "get_vehicles",
        "label": "Vehicle",
        "label_plural": "Vehicles",
    },
}


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------

def read_uploaded_csv(uploaded_file):
    """Returns (headers, rows) or raises ValueError with a user-facing message."""
    if not uploaded_file.name.lower().endswith(".csv"):
        raise ValueError("Please upload a .csv file.")
    if uploaded_file.size > 5 * 1024 * 1024:
        raise ValueError("File is too large. Maximum size is 5MB.")

    try:
        raw = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("Could not read the file. Please save it as UTF-8 CSV and try again.")

    rows = list(csv.reader(io.StringIO(raw)))
    if not rows:
        raise ValueError("The CSV file is empty.")

    headers = [h.strip() for h in rows[0] if h and h.strip()]
    if not headers:
        raise ValueError("No column headers were found in the CSV file.")

    data_rows = rows[1:]
    if not data_rows:
        raise ValueError("No data rows were found below the header row.")
    if len(data_rows) > 2000:
        raise ValueError("Maximum 2000 rows allowed per upload.")

    return headers, data_rows


def auto_map_headers(headers, fields):
    """Best-effort CSV-column -> model-field mapping based on normalized label/key match."""
    mapping = {}
    normalized_headers = {_normalize(h): h for h in headers}
    for field in fields:
        key_norm = _normalize(field["key"])
        label_norm = _normalize(field["label"])
        match = normalized_headers.get(label_norm) or normalized_headers.get(key_norm)
        if not match:
            # loose contains-match as a fallback
            for norm, original in normalized_headers.items():
                if norm and (norm in label_norm or label_norm in norm):
                    match = original
                    break
        if match:
            mapping[field["key"]] = match
    return mapping


# ---------------------------------------------------------------------------
# Import processing
# ---------------------------------------------------------------------------

def summarize_mapping(entity_key, headers, mapping):
    """
    Describes, before anything is touched, which model fields are mapped and
    which CSV columns will simply be ignored. Used on the review/confirm step
    so the user sees exactly what will and won't be imported.
    """
    config = ENTITIES[entity_key]
    mapped_headers = set(mapping.values())

    mapped_fields = [f for f in config["fields"] if f["key"] in mapping]
    unmapped_required = [f["label"] for f in config["fields"] if f.get("required") and f["key"] not in mapping]
    unmapped_optional = [f["label"] for f in config["fields"] if not f.get("required") and f["key"] not in mapping]
    ignored_columns = [h for h in headers if h not in mapped_headers]

    return {
        "mapped_fields": mapped_fields,
        "unmapped_required": unmapped_required,
        "unmapped_optional": unmapped_optional,
        "ignored_columns": ignored_columns,
    }


def _parse_row(config, fields_by_key, header_index, row, fk_cache, commit):
    """
    Parses one CSV row against the mapping.

    Two different kinds of problems are tracked separately:
      - `dropped`: a single mapped field had a bad value (e.g. an unparseable
        date). That ONE field is left blank; the row still imports.
      - `hard_errors`: a *required* field is missing/blank. The whole row is
        skipped.

    fk fields are only resolved against the database (get_or_create) when
    commit=True, so previewing an import never creates Company/Location/etc
    rows for an import the user ends up cancelling.
    """
    dropped = []
    hard_errors = []
    values = {}
    preview = {}

    for field_key, csv_header in header_index["mapping"].items():
        if not csv_header or csv_header not in header_index["headers"]:
            continue
        field = fields_by_key.get(field_key)
        if not field:
            continue
        col_index = header_index["headers"][csv_header]
        raw_value = row[col_index].strip() if col_index < len(row) else ""

        if not raw_value:
            values[field_key] = None
            continue

        kind = field["kind"]
        if kind == "text":
            values[field_key] = raw_value
            preview[field["label"]] = raw_value
        elif kind == "int":
            parsed, err = parse_csv_int(raw_value)
            if err:
                dropped.append((field["label"], err))
            else:
                values[field_key] = parsed
                preview[field["label"]] = str(parsed)
        elif kind == "date":
            parsed, err = parse_csv_date(raw_value)
            if err:
                dropped.append((field["label"], err))
            else:
                values[field_key] = parsed
                preview[field["label"]] = parsed.isoformat()
        elif kind == "bool":
            parsed, err = parse_csv_bool(raw_value)
            if err:
                dropped.append((field["label"], err))
            else:
                values[field_key] = parsed
                preview[field["label"]] = "Yes" if parsed else "No"
        elif kind == "choice":
            match = next((c for c in field["choices"] if c.lower() == raw_value.lower()), None)
            if not match:
                dropped.append(
                    (field["label"], f"'{raw_value}' is not one of {', '.join(field['choices'])}")
                )
            else:
                values[field_key] = match
                preview[field["label"]] = match
        elif kind == "fk":
            if commit:
                obj, err = resolve_fk(field["fk_model"], field["fk_field"], raw_value, fk_cache)
                if err:
                    dropped.append((field["label"], err))
                else:
                    values[field_key] = obj
            else:
                # Dry-run: don't touch the database, just show what will be
                # looked up / created once the import is confirmed.
                values[field_key] = raw_value
            preview[field["label"]] = raw_value

    required_missing = [
        f["label"] for f in config["fields"]
        if f.get("required") and not values.get(f["key"])
    ]
    if required_missing:
        hard_errors.append(f"Missing required field(s): {', '.join(required_missing)}")

    return values, dropped, hard_errors, preview


def process_rows(entity_key, headers, rows, mapping, commit=False):
    """
    Validates every row against the mapping. When commit=False (preview/dry-run)
    nothing is written to the database. When commit=True, accepted rows are saved
    (a row with only soft field-level problems still saves, just without those
    field values).

    Returns:
        {
          created, updated, skipped,
          errors: [(row_number, message)],           # rows skipped entirely
          row_details: [                              # used by the review/preview page
              {row_number, status: "ok"|"warning"|"error", errors: [...],
               dropped_fields: [(label, reason), ...], preview: {label: value}, action}
          ],
          field_error_counts: {field_label: count},   # which mapped fields cause the most trouble
          dropped_field_count: int,                   # total individual fields left blank
          warned_rows: int,                            # rows that imported but had a field dropped
        }
    """
    config = ENTITIES[entity_key]
    model = config["model"]
    fields_by_key = {f["key"]: f for f in config["fields"]}
    natural_key = config["natural_key"]
    header_index = {"headers": {h: i for i, h in enumerate(headers)}, "mapping": mapping}
    fk_cache = {}

    results = {
        "created": 0, "updated": 0, "skipped": 0,
        "errors": [], "row_details": [], "field_error_counts": {},
        "dropped_field_count": 0, "warned_rows": 0,
    }

    for row_num, row in enumerate(rows, start=2):  # row 1 is the header
        values, dropped, hard_errors, preview = _parse_row(
            config, fields_by_key, header_index, row, fk_cache, commit
        )

        for label, reason in dropped:
            results["field_error_counts"][label] = results["field_error_counts"].get(label, 0) + 1

        if hard_errors:
            results["errors"].append((row_num, "; ".join(hard_errors)))
            results["skipped"] += 1
            results["row_details"].append({
                "row_number": row_num, "status": "error",
                "errors": hard_errors, "dropped_fields": [], "preview": preview,
            })
            continue

        if dropped:
            results["dropped_field_count"] += len(dropped)
            results["warned_rows"] += 1

        is_new = True
        try:
            instance = None
            is_restoring = False
            key_value = values.get(natural_key)
            if key_value:
                instance = model.objects.filter(**{f"{natural_key}__iexact": str(key_value)}).first()
                is_restoring = bool(instance and instance.is_deleted)

            is_new = instance is None

            if commit:
                if is_new:
                    instance = model()
                elif is_restoring:
                    instance.is_deleted = False
                    instance.deleted_at = None
                    instance.deleted_by = None
                for field_key, value in values.items():
                    setattr(instance, field_key, value)
                instance.save()

            results["created" if is_new else "updated"] += 1
            results["row_details"].append({
                "row_number": row_num,
                "status": "warning" if dropped else "ok",
                "errors": [], "dropped_fields": dropped, "preview": preview,
                "action": "create" if is_new else "restore" if is_restoring else "update",
            })
        except IntegrityError:
            logger.exception("CSV import row %s hit a uniqueness constraint", row_num)
            natural_label = "CNIC" if entity_key == "driver" else "TL_Number" if entity_key == "vehicle" else natural_key
            message = f"Row {row_num}: duplicate {natural_label} already exists."
            results["errors"].append((row_num, message))
            results["skipped"] += 1
            results["row_details"].append({
                "row_number": row_num, "status": "error",
                "errors": [message], "dropped_fields": dropped, "preview": preview,
            })
        except Exception:  # noqa: BLE001 - surface any save-time error per row
            logger.exception("CSV import row %s failed", row_num)
            results["errors"].append((row_num, f"Row {row_num}: could not be saved. See server logs."))
            results["skipped"] += 1
            results["row_details"].append({
                "row_number": row_num, "status": "error",
                "errors": [f"Row {row_num}: could not be saved. See server logs."], "dropped_fields": dropped, "preview": preview,
            })

    return results


# ---------------------------------------------------------------------------
# Export processing
# ---------------------------------------------------------------------------

def build_export_response(entity_key, selected_keys=None):
    from django.http import HttpResponse

    config = ENTITIES[entity_key]
    columns = config["export_columns"]
    if selected_keys:
        columns = [c for c in columns if c[0] in selected_keys] or columns

    queryset = config["model"].objects.filter(is_deleted=False)

    response = HttpResponse(content_type="text/csv")
    filename = f"{entity_key}s_export.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([label for _key, label, _accessor in columns])
    for obj in queryset.iterator():
        writer.writerow([accessor(obj) for _key, _label, accessor in columns])

    return response