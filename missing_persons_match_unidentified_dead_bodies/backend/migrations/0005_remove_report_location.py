# Generated by Django 4.0.8 on 2023-01-09 13:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_report_year'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='report',
            name='location',
        ),
    ]
