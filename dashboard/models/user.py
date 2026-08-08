from django.contrib.auth.models import User
from django.db import models


class User_Image(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    img = models.ImageField(max_length=500, null=True, upload_to="user_images/")
