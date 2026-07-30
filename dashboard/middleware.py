from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of URLs that don't require authentication.
        excluded_paths = [reverse("login")]

        is_public_path = (
            request.path in excluded_paths
            or request.path.startswith(settings.STATIC_URL)
            or request.path.startswith(settings.MEDIA_URL)
        )

        # If the user is not authenticated and the path is not excluded
        if not request.user.is_authenticated and not is_public_path:
            return redirect("login")

        response = self.get_response(request)
        return response
