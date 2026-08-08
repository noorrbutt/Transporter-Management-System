from datetime import date, timedelta
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from dashboard.middleware import LoginRequiredMiddleware
from dashboard.models import Driver
from dashboard.services import (
    compute_driver_expiry_statuses,
    compute_vehicle_expiry_statuses,
)
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


class ExpiryStatusServiceTests(SimpleTestCase):
    def test_compute_driver_expiry_statuses_returns_expected_status_keys(self):
        driver = SimpleNamespace(
            CNIC_Validity=date.today() + timedelta(days=10),
            DDC_Issue_Date=date.today() + timedelta(days=100),
            HTV_License_Issue_Date=date.today() + timedelta(days=200),
            HTV_License_Expiry_Date=date.today() - timedelta(days=1),
            DDC_Expiry_Date=date.today() + timedelta(days=20),
            Report_Date=date.today() + timedelta(days=30),
            Expiry_Date=date.today() + timedelta(days=40),
            Joining_Date=date.today() + timedelta(days=50),
            Salary_Increment_Date=date.today() + timedelta(days=60),
            Leave_Date=date.today() + timedelta(days=70),
            Leave_Resume=date.today() + timedelta(days=80),
        )

        statuses = compute_driver_expiry_statuses(driver)

        self.assertEqual(statuses["CNIC_Validity_status"], "Close to Expiry")
        self.assertEqual(statuses["HTV_License_Expiry_Date_status"], "Expired")
        self.assertEqual(statuses["DDC_Date_status"], "Close to Expiry")

    def test_compute_vehicle_expiry_statuses_returns_expected_status_keys(self):
        vehicle = SimpleNamespace(
            TAX_PAID_Date=date.today() + timedelta(days=10),
            FITNISSE_Date=date.today() + timedelta(days=100),
            INSURANCE_Date=date.today() - timedelta(days=1),
            DIP_CHART_Date=date.today() + timedelta(days=20),
            Q_FOM_Date=date.today() + timedelta(days=30),
            Route_Permit_Date=date.today() + timedelta(days=40),
        )

        statuses = compute_vehicle_expiry_statuses(vehicle)

        self.assertEqual(statuses["tax_expiry_status"], "Close to Expiry")
        self.assertEqual(statuses["road_insurance_status"], "Expired")
        self.assertEqual(statuses["Route_status"], "Close to Expiry")


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
