from django.db.models.signals import post_save
from django.dispatch import receiver

from missing_persons_match_unidentified_dead_bodies.backend.models import Report

from .tasks import (
    add_description_search_vector_to_report,
    add_icon_to_report,
    add_tokens_to_report,
)


@receiver(post_save, sender=Report)
def report_created_add_icon(sender, instance, **kwargs):
    print("callback 1")
    if not instance.icon:
        add_icon_to_report.apply_async(args=[instance.pk], countdown=5)


@receiver(post_save, sender=Report)
def report_created_add_description_search_vector(sender, instance, **kwargs):
    print("callback 2")
    if not instance.description_search_vector:
        add_description_search_vector_to_report.apply_async(
            args=[instance.pk], countdown=5
        )
    else:
        print("It already  has a DSV")


@receiver(post_save, sender=Report)
def report_created_add_tokens(sender, instance, **kwargs):
    print("callback 3")
    if not instance.tokens.exists():
        add_tokens_to_report.apply_async(args=[instance.pk], countdown=5)
