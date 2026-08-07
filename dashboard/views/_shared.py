import calendar
import json
import logging
from datetime import date, datetime
from functools import wraps
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

try:
    from django_ratelimit.decorators import ratelimit
    from django_ratelimit.exceptions import Ratelimited
except ImportError:
    def ratelimit(*args, **kwargs):
        def decorator(view_func):
            return view_func

        return decorator


    class Ratelimited(Exception):
        pass

from ..models import (
    Company,
    Driver,
    DriverDrillCompletion,
    DriverTrainingCompletion,
    Driver_Violation,
    Location,
    Procedure,
    User_Image,
    Vehicle,
    VehicleMaker,
    VehicleOwner,
    Violations,
    annual_drill,
    annual_training,
    driver_tool_box_meeting_attended,
    tool_box_meeting_topics,
)

Image.MAX_IMAGE_PIXELS = 20_000_000

logger = logging.getLogger(__name__)


def _prepare_uploaded_image(request, uploaded_file):
    if not uploaded_file:
        return None

    try:
        uploaded_file.file.seek(0)
        with Image.open(uploaded_file.file) as image:
            image.verify()

        uploaded_file.file.seek(0)
        with Image.open(uploaded_file.file) as image:
            if image.format not in {"JPEG", "PNG"}:
                raise UnidentifiedImageError("Unsupported image format")

            image.load()
            width, height = image.size
            new_size = min(width, height)
            left = (width - new_size) / 2
            top = (height - new_size) / 2
            right = (width + new_size) / 2
            bottom = (height + new_size) / 2
            image = image.crop((left, top, right, bottom))
            image = image.resize((200, 200), Image.LANCZOS)

            image_data = BytesIO()
            image.save(image_data, format="JPEG")
            image_data.seek(0)
            return ContentFile(image_data.getvalue(), name=uploaded_file.name)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        messages.error(request, "Uploaded file is not a valid image.")
        return None


def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def _ratelimit_catch(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Ratelimited:
            messages.error(request, "Too many attempts. Try again later.")
            return render(request, "user/login.html", status=429)

    return _wrapped
