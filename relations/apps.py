from django.apps import AppConfig


class RelationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "relations"

    def ready(self) -> None:
        from .signals import on_following_created

        return super().ready()
