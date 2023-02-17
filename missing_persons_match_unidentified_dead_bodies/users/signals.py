from allauth.account.models import EmailAddress
from django.contrib.auth.models import Group
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def add_user_to_group(sender, instance, **kwargs):
    group, created = Group.objects.get_or_create(name=instance.category)
    instance.groups.set([group])


@receiver(post_save, sender=User)
def verify_user(sender, instance, **kwargs):
    try:
        email_address = EmailAddress.objects.filter(user=instance)
        for email in email_address:
            email.verified = True
            email.save()
    except Exception as e:
        print(str(e))


@receiver(pre_delete, sender=User)
def delete_user_email_address(sender, instance, **kwargs):
    try:
        email_address = EmailAddress.objects.filter(user=instance)
        for email in email_address:
            email.delete()
    except Exception as e:
        print(str(e))
