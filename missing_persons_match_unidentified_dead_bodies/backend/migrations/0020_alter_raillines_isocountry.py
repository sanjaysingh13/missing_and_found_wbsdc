# Generated by Django 4.0.8 on 2023-01-27 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0019_raillines'),
    ]

    operations = [
        migrations.AlterField(
            model_name='raillines',
            name='ISOCOUNTRY',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
