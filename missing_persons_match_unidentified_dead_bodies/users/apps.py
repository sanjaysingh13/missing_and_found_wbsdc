from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "missing_persons_match_unidentified_dead_bodies.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import missing_persons_match_unidentified_dead_bodies.users.signals  # noqa F401
        except ImportError:
            pass
