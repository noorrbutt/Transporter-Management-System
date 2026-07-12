from django.test import TestCase, Client
from django.contrib.auth.models import User
from dashboard.models import Driver


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
