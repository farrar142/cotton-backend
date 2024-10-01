from typing import Self
from django.db.transaction import atomic
from django.db import models
from commons.lock import with_lock
from users.models import User
from .models import Follow


def get_key(self: "FollowService", target_user: User):
    return f"following:{self.user.pk}:{target_user.pk}"


class FollowService:
    def __init__(self, user: User):
        self.user = user

    @with_lock(get_key)
    def follow(self, target_user: User):
        if not self.user.followings.filter(id=target_user.pk).exists():
            self.user.followings.add(target_user)

    @with_lock(get_key)
    def unfollow(self, target_user: User):
        if self.user.followings.filter(id=target_user.pk).exists():
            Follow.objects.filter(
                following_to=target_user, followed_by=self.user
            ).delete()

    def get_users_followers(self, user: User):
        return (
            User.concrete_queryset(self.user)
            .annotate(
                followed_by_created_at=models.Subquery(
                    Follow.objects.filter(
                        followed_by=models.OuterRef("pk"), following_to=user
                    ).values("created_at")
                )
            )
            .filter(followings=user)
        )

    def get_users_followings(self, user: User):
        return (
            User.concrete_queryset(self.user)
            .annotate(
                following_created_at=models.Subquery(
                    Follow.objects.filter(
                        following_to=models.OuterRef("pk"), followed_by=user
                    ).values("created_at")
                )
            )
            .filter(followers__followed_by_id=user)
        )

    def get_mutual_followings(self):
        return User.concrete_queryset(self.user).filter(
            followers__followed_by_id=self.user, followings=self.user
        )
