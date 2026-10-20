from django.apps import AppConfig


class ReleasesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "releases"
    verbose_name = "Releases"

    def ready(self) -> None:
        from . import signals  # noqa: F401
