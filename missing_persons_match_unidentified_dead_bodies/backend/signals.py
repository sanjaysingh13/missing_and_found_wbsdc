from django.db.models.signals import post_save
from django.dispatch import receiver

from missing_persons_match_unidentified_dead_bodies.backend.models import Match, Report

from .tasks import add_icon_to_report, send_matched_mail


@receiver(post_save, sender=Report)
def report_created_add_icon(sender, instance, **kwargs):
    if not instance.icon:
        add_icon_to_report.apply_async(args=[instance.pk], countdown=5)


@receiver(post_save, sender=Match)
def report_send_mail_for_match(sender, instance, **kwargs):
    if not instance.mail_sent:
        send_matched_mail.apply_async(args=[instance.pk], countdown=5)


# @receiver(post_save, sender=Report)
# def report_created_add_description_search_vector(sender, instance, **kwargs):
#     print("callback 2")
#     if not instance.description_search_vector:
#         add_description_search_vector_to_report.apply_async(
#             args=[instance.pk], countdown=5
#         )
#     else:
#         print("It already  has a DSV")
