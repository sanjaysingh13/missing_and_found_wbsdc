# Generated by Django 4.0.8 on 2023-02-11 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0033_emailrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='publicreport',
            name='reconciled',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='report',
            name='reconciled',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]