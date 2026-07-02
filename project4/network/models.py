from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Post(models.Model):
    title = models.CharField(max_length=50)
    content = models.CharField(max_length=500)
    
    def __str__(self):
        return f"{self.title}: {self.content}"