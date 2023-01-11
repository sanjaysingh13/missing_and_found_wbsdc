from django.db.models.signals import pre_save
from django.dispatch import receiver

from missing_persons_match_unidentified_dead_bodies.backend.models import Report

from .tasks import add_icon_to_report


@receiver(pre_save, sender=Report)
def report_created_add_icon(sender, instance, **kwargs):
    if not instance.icon:
        add_icon_to_report.apply_async(args=[instance.pk], countdown=5)
