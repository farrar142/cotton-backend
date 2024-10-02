from django.apps import AppConfig


class PostsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "posts"

    def ready(self) -> None:
        from .signals import (
            on_favorite_created,
            on_post_created,
            on_repost_created,
            on_mention_created,
        )
