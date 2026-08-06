from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from . import csv_io

SESSION_KEY = "csv_import_data"  # {entity, headers, rows, mapping}


def _get_entity_or_404(entity_key):
    if entity_key not in csv_io.ENTITIES:
        raise Http404("Unknown import/export entity")
    return csv_io.ENTITIES[entity_key]


def _list_url(config, entity_key):
    return reverse(config["list_url"], args=["all"]) if entity_key == "vehicle" else reverse(config["list_url"])


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def csv_export(request, entity_key):
    """
    GET  /csv/<entity>/export/            -> full export, all columns
    GET  /csv/<entity>/export/?fields=a,b -> export only the selected columns
    """
    _get_entity_or_404(entity_key)
    selected = request.GET.get("fields")
    selected_keys = [f for f in selected.split(",") if f] if selected else None
    return csv_io.build_export_response(entity_key, selected_keys)


# ---------------------------------------------------------------------------
# Import: step 1 - upload (triggered directly from the Actions menu's hidden
# file input, no intermediate "choose file" page)
# ---------------------------------------------------------------------------

def csv_import_upload(request, entity_key):
    config = _get_entity_or_404(entity_key)
    list_url = _list_url(config, entity_key)

    if request.method != "POST":
        return redirect(list_url)

    uploaded_file = request.FILES.get("csv_file")
    if not uploaded_file:
        messages.error(request, "Please choose a CSV file to upload.")
        return redirect(list_url)

    try:
        headers, rows = csv_io.read_uploaded_csv(uploaded_file)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect(list_url)

    request.session[SESSION_KEY] = {
        "entity": entity_key,
        "headers": headers,
        "rows": rows,
        "mapping": {},
    }
    request.session.modified = True

    return redirect("csv_import_map", entity_key=entity_key)


# ---------------------------------------------------------------------------
# Import: step 2 - map CSV columns to fields
# ---------------------------------------------------------------------------

def csv_import_map(request, entity_key):
    config = _get_entity_or_404(entity_key)
    list_url = _list_url(config, entity_key)

    session_data = request.session.get(SESSION_KEY)
    if not session_data or session_data.get("entity") != entity_key:
        messages.error(request, "Please upload a CSV file first.")
        return redirect(list_url)

    headers = session_data["headers"]
    rows = session_data["rows"]

    if request.method == "POST":
        mapping = {
            field["key"]: request.POST.get(f"map__{field['key']}", "").strip()
            for field in config["fields"]
        }
        mapping = {k: v for k, v in mapping.items() if v}

        required_keys = [f["key"] for f in config["fields"] if f.get("required")]
        missing = [
            f["label"] for f in config["fields"]
            if f["key"] in required_keys and f["key"] not in mapping
        ]
        if missing:
            messages.error(request, f"Please map the required field(s): {', '.join(missing)}")
        else:
            session_data["mapping"] = mapping
            request.session[SESSION_KEY] = session_data
            request.session.modified = True
            return redirect("csv_import_review", entity_key=entity_key)

    # Prefill from a previously chosen mapping (e.g. user came back from the
    # review step to adjust something) or fall back to the best-guess auto-map.
    existing_mapping = session_data.get("mapping") or {}
    auto_mapping = existing_mapping or csv_io.auto_map_headers(headers, config["fields"])

    context = {
        "entity_key": entity_key,
        "entity": config,
        "headers": headers,
        "fields": config["fields"],
        "auto_mapping": auto_mapping,
        "total_rows": len(rows),
        "preview_rows": rows[:5],
        "list_url": list_url,
    }
    return render(request, "csv_io/import_map.html", context)


# ---------------------------------------------------------------------------
# Import: step 3 - review (dry run: nothing is saved yet)
# ---------------------------------------------------------------------------

def csv_import_review(request, entity_key):
    config = _get_entity_or_404(entity_key)
    list_url = _list_url(config, entity_key)

    session_data = request.session.get(SESSION_KEY)
    if not session_data or session_data.get("entity") != entity_key or not session_data.get("mapping"):
        messages.error(request, "Please upload a CSV file and map its columns first.")
        return redirect(list_url)

    headers = session_data["headers"]
    rows = session_data["rows"]
    mapping = session_data["mapping"]

    dry_run_results = csv_io.process_rows(entity_key, headers, rows, mapping, commit=False)
    mapping_summary = csv_io.summarize_mapping(entity_key, headers, mapping)

    context = {
        "entity_key": entity_key,
        "entity": config,
        "total_rows": len(rows),
        "results": dry_run_results,
        "mapping_summary": mapping_summary,
        "list_url": list_url,
    }
    return render(request, "csv_io/import_review.html", context)


# ---------------------------------------------------------------------------
# Import: step 4 - confirm (actually saves valid rows)
# ---------------------------------------------------------------------------

def csv_import_confirm(request, entity_key):
    config = _get_entity_or_404(entity_key)
    list_url = _list_url(config, entity_key)

    if request.method != "POST":
        return redirect(list_url)

    session_data = request.session.get(SESSION_KEY)
    if not session_data or session_data.get("entity") != entity_key or not session_data.get("mapping"):
        messages.error(request, "Your import session expired. Please upload the CSV again.")
        return redirect(list_url)

    headers = session_data["headers"]
    rows = session_data["rows"]
    mapping = session_data["mapping"]

    results = csv_io.process_rows(entity_key, headers, rows, mapping, commit=True)

    del request.session[SESSION_KEY]
    request.session.modified = True

    context = {
        "entity_key": entity_key,
        "entity": config,
        "results": results,
        "total_rows": len(rows),
        "list_url": list_url,
    }
    return render(request, "csv_io/import_results.html", context)


def csv_import_cancel(request, entity_key):
    config = _get_entity_or_404(entity_key)
    request.session.pop(SESSION_KEY, None)
    request.session.modified = True
    return redirect(_list_url(config, entity_key))