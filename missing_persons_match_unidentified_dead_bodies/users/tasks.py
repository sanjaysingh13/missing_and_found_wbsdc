from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

from config import celery_app

User = get_user_model()


@celery_app.task()
def verify_users():
    er = EmailAddress.objects.filter(verified=False)
    for e in er:
        e.verified = True
        e.save()
