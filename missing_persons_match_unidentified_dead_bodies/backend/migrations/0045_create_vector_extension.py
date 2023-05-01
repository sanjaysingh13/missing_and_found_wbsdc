from django.db import migrations
from pgvector.django import VectorExtension

class Migration(migrations.Migration):
    dependencies = [
        ("backend", '0044_comment_telephone'),
    ]

    operations = [
        VectorExtension(),
    ]
