from django.apps import AppConfig


class BackendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "missing_persons_match_unidentified_dead_bodies.backend"

    def ready(self):
        import missing_persons_match_unidentified_dead_bodies.backend.signals  # noqa
