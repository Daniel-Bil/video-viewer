from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image_id = models.PositiveIntegerField(default=0)  # Stores the ID of the selected image

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_profile_image(self):
        # Predefined images, can be stored as static paths
        images = {
            0: 'static/images/trex.png',
            1: 'static/images/triceratops.png',
            2: 'static/images/stegozaur.png',
        }
        return images.get(self.image_id, 'static/images/trex.png')
