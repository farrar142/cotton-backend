from django.db import models

from users.models import User


# Create your models here.
class Follow(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["following_to", "created_at"]),
            models.Index(fields=["followed_by", "created_at"]),
            models.Index(fields=["following_to", "followed_by"]),
        ]

    created_at = models.DateTimeField(auto_now_add=True)
    following_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers"
    )
    followed_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f":{self.pk} user  {self.followed_by} following {self.following_to} : {self.created_at}"
