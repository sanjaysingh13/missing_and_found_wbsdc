# from django.dispatch import receiver
# from django.db.models.signals import post_save,pre_save
# from missing_persons_match_unidentified_dead_bodies.backend.models import Report
# from ccs_aws.users.models import PoliceStation as ps, District as distt, User as us
# import uuid as unique_universal_identifier
# import datetime

# @receiver(pre_save, sender=Report)
# def report_created_add_year(sender, instance,  **kwargs):
#     if instance.entry_date:
#         instance.year = str(instance.entry_date.year)[-2:]
