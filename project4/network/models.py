from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    following = models.ManyToManyField(
        "User",
        blank=True,
        related_name="followed_by"
    )
    liked_posts = models.ManyToManyField(
        "Post",
        blank=True,
        related_name="liked_by"
    )

    @property
    def followers_count(self):
        return self.followed_by.count()
    
    @property
    def following_count(self):
        return self.following.count()

class Post(models.Model):
    content = models.CharField(max_length=500)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.content
    
    @property
    def likes_count(self):
        return self.liked_by.count()