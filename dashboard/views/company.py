from ._shared import (
    Company,
    get_object_or_404,
    HttpResponseRedirect,
    logger,
    messages,
    redirect,
    render,
    superuser_required,
    timezone,
    transaction,
)


def get_company(request):

    companies = Company.objects.filter(is_deleted=False)
    context = {
        "companies": companies,
    }
    return render(request, "company/company.html", context)


@superuser_required
@transaction.atomic
def add_company(request):
    try:
        if request.method == "POST":
            company = Company()
            company.cabb = request.POST.get("cabb")
            company.cname = request.POST.get("company_name")
            company.save()

            return HttpResponseRedirect("/company")
        else:
            return render(request, "company/add_company.html", {"action": "Add"})
    except Exception as e:
        logger.exception("Operation failed in %s", request.path)
        messages.error(
            request, "Something went wrong. Please check your input and try again."
        )
        return redirect(request.path)


@superuser_required
@transaction.atomic
def edit_company(request, company_id):
    company = get_object_or_404(Company, cid=company_id)

    try:
        if request.method == "POST":
            cabb = request.POST.get("cabb")
            cname = request.POST.get("company_name")

            company.cabb = cabb
            company.cname = cname
            company.save()

            return HttpResponseRedirect("/company")
    except Exception as e:
        messages.error(request, f"Operation failed: {str(e)}")
        return redirect(request.path)
    return render(
        request, "company/add_company.html", {"company": company, "action": "Edit"}
    )


@superuser_required
@transaction.atomic
def delete_company(request, company_id):
    if request.method != "POST":
        return redirect("/company")
    entry = get_object_or_404(Company, cid=company_id)
    try:
        entry.is_deleted = True
        entry.deleted_at = timezone.now()
        entry.deleted_by = request.user
        entry.save()
    except Exception:
        pass
    return redirect("/company")
