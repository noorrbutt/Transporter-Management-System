from ._shared import (
    Driver,
    Driver_Violation,
    Violations,
    HttpResponseRedirect,
    get_object_or_404,
    logger,
    messages,
    redirect,
    render,
    reverse,
    superuser_required,
    transaction,
)


def get_violation(request):
    violations = Violations.objects.all()
    context = {"violations": violations}
    return render(request, "violation/violations.html", context)


@superuser_required
@transaction.atomic
def add_violation(request):
    try:
        if request.method == "POST":
            violation_type = request.POST.get("violation_type")
            if not violation_type or not violation_type.strip():
                messages.error(request, "Violation type cannot be empty.")
                return redirect(request.path)
            Violations.objects.create(violation_type=violation_type.strip())
            return redirect("/violations")
        else:
            return render(request, "violation/add_violation.html")
    except Exception as e:
        messages.error(request, f"Operation failed: {str(e)}")
        return redirect(request.path)


@superuser_required
@transaction.atomic
def add_driver_violation(request, D_ID):
    driver = get_object_or_404(Driver, D_ID=D_ID)
    violation = Violations.objects.all()
    try:
        if request.method == "POST":
            violation_type = request.POST.get("violationType")
            violation_obj = Violations.objects.get(violation_type=violation_type)
            violation_date = request.POST.get("violationDate")
            details = request.POST.get("details")
            driver_violation = Driver_Violation(
                driver=driver,
                violation=violation_obj,
                violation_date=violation_date,
                violation_notes=details,
            )
            driver_violation.save()
            driver_view_url = reverse("driverview", args=[D_ID])
            return HttpResponseRedirect(driver_view_url)
        else:
            context = {"driver": driver, "violations": violation}
            return render(request, "violation/add_driver_violation.html", context)
    except Exception as e:
        logger.exception("Operation failed in %s", request.path)
        messages.error(
            request, "Something went wrong. Please check your input and try again."
        )
        return redirect(request.path)
