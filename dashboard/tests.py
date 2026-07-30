from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from dashboard.middleware import LoginRequiredMiddleware
from dashboard.models import Driver
from dashboard.views import superuser_required


class SoftDeleteRegressionTest(TestCase):
    def test_soft_delete_driver_hides_from_listing_but_keeps_record(self):
        admin = User.objects.create_user(username="admin", password="pass")
        admin.is_superuser = True
        admin.save()

        driver = Driver.objects.create(D_Name="Test Driver")

        client = Client()
        client.force_login(admin)

        resp = client.get("/drivers")
        self.assertIn(driver, resp.context["drivers"])

        # perform delete via view
        client.post(f"/deletedriver/{driver.D_ID}/")

        driver.refresh_from_db()
        self.assertTrue(driver.is_deleted)
        self.assertIsNotNone(driver.deleted_at)
        self.assertEqual(driver.deleted_by, admin)

        resp = client.get("/drivers")
        self.assertNotIn(driver, resp.context["drivers"])


class SuperuserRequiredDecoratorTests(TestCase):
    def test_non_superuser_authenticated_request_is_denied(self):
        @superuser_required
        def sample_view(request):
            return HttpResponse("ok")

        request = RequestFactory().get("/")
        request.user = User.objects.create_user(username="staff", password="pass")
        request.user.is_superuser = False
        request.user.save()

        with self.assertRaises(PermissionDenied):
            sample_view(request)

    def test_superuser_authenticated_request_is_allowed(self):
        @superuser_required
        def sample_view(request):
            return HttpResponse("ok")

        request = RequestFactory().get("/")
        request.user = User.objects.create_user(username="admin", password="pass")
        request.user.is_superuser = True
        request.user.save()

        response = sample_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")


class LoginRequiredMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = LoginRequiredMiddleware(lambda request: HttpResponse("ok"))

    def test_static_and_media_paths_are_exempt_from_auth(self):
        for path in ["/static/css/app-overrides.css", "/media/driver_images/sample.png"]:
            request = self.factory.get(path)
            request.user = AnonymousUser()

            response = self.middleware(request)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b"ok")

    def test_login_path_remains_public(self):
        request = self.factory.get(reverse("login"))
        request.user = AnonymousUser()

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_protected_paths_still_redirect(self):
        request = self.factory.get("/vehicles/active/")
        request.user = AnonymousUser()

        response = self.middleware(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))
