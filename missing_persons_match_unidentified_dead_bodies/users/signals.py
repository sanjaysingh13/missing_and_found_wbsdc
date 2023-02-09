from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def add_user_to_group(sender, instance, **kwargs):
    group, created = Group.objects.get_or_create(name=instance.category)
    instance.groups.set([group])
