from dashboard.forms import UserForm

from ._shared import (
    JsonResponse,
    Paginator,
    User,
    User_Image,
    _prepare_uploaded_image,
    _ratelimit_catch,
    authenticate,
    get_object_or_404,
    login,
    login_required,
    logout,
    messages,
    redirect,
    render,
    ratelimit,
    superuser_required,
    validate_password,
)
from django.core.exceptions import ValidationError


@_ratelimit_catch
@ratelimit(key="ip", rate="5/m", method="POST", block=True)
def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            messages.error(request, "Invalid login credentials. Please try again.")

    return render(request, "user/login.html")


def logout_user(request):
    logout(request)
    return redirect("/loginuser")


@superuser_required
def adduser(request):

    if request.method == "POST":
        form = UserForm(request.POST, request.FILES)
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect(request.path)

        password = form.cleaned_data.get("password")
        if not password:
            messages.error(request, "Password cannot be blank.")
            return redirect(request.path)

        try:
            validate_password(password, user=None)
        except ValidationError as exc:
            for message in exc.messages:
                messages.error(request, message)
            return redirect(request.path)

        user = form.save()

        user_image = request.FILES.get("user_image")
        if user_image:
            user_image_obj = User_Image(user=user)

            if user_image.size > 5 * 1024 * 1024:
                messages.error(request, "Image must be smaller than 5MB.")
                return redirect(request.path)

            image_file = _prepare_uploaded_image(request, user_image)
            if image_file is None:
                return redirect(request.path)

            user_image_obj.img.save(user_image.name, image_file)
            user_image_obj.save()

        return redirect("/allusers")

    return render(request, "user/adduser.html", {"heading": "Adding User"})


@superuser_required
def deleteuser(request, id):
    if request.method != "POST":
        return redirect("/allusers")
    user = get_object_or_404(User, id=id)
    user.delete()

    return redirect("/allusers")


@superuser_required
def edituser(request, id):

    user = get_object_or_404(User, id=id)

    flag = True
    try:
        user_image_obj = User_Image.objects.get(user=user)
        flag = True
    except User_Image.DoesNotExist:
        user_image_obj = User_Image(user=user)
        flag = False

    if request.method == "POST":
        form = UserForm(request.POST, request.FILES, instance=user)
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect(request.path)

        password = form.cleaned_data.get("password")
        if password:
            try:
                validate_password(password, user)
            except ValidationError as exc:
                for message in exc.messages:
                    messages.error(request, message)
                return redirect(request.path)

        user = form.save(instance=user)

        user_image = request.FILES.get("user_image")
        if user_image:
            if user_image.size > 5 * 1024 * 1024:
                messages.error(request, "Image must be smaller than 5MB.")
                return redirect(request.path)

            image_file = _prepare_uploaded_image(request, user_image)
            if image_file is None:
                return redirect(request.path)

            if flag:
                user_image_obj.delete()

            user_image_obj.img.save(user_image.name, image_file)
            user_image_obj.save()

        return redirect("/allusers")

    initial_data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "access_level": "Full Access" if user.is_superuser else "Read Only Access",
        "status": "Active" if user.is_active else "Disabled",
    }

    context = {
        "user": user,
        "initial_data": initial_data,
        "user_img": user_image_obj.img,
        "heading": "Editing User",
    }

    return render(request, "user/adduser.html", context)


def check_username(request):
    username = request.GET.get("username", None)
    data = {"is_taken": User.objects.filter(username=username).exists()}
    return JsonResponse(data)


@login_required(login_url="/loginuser")
def allusers(request):

    users = User.objects.all()
    paginator = Paginator(users, 50)
    users = paginator.get_page(request.GET.get("page"))
    user_data = []

    for user in users:
        user_image = User_Image.objects.filter(user=user).first()

        user_info = {
            "user": user,
            "user_image": user_image,
        }
        user_data.append(user_info)

    context = {"user_data": user_data, "users": users, "page_obj": users}
    return render(request, "user/users.html", context)
