from django.conf import settings
from django.core.cache import cache

from missing_persons_match_unidentified_dead_bodies.users.models import PoliceStation


def settings_context(_request):
    """Settings available by default to the templates context."""
    # Note: we intentionally do NOT expose the entire settings
    # to prevent accidental leaking of sensitive information
    ps_list = cache.get("ps_list")
    if not ps_list:
        ps_list = [
            (ps["id"], ps["ps_with_distt"])
            for ps in PoliceStation.objects.all().order_by("ps_with_distt").values()
        ]
        cache.set("ps_list", ps_list, None)
    return {
        "DEBUG": settings.DEBUG,
        "ps_list": ps_list,
        "admin_users": ["ADMIN", "CID_ADMIN"],
    }  # explicit
