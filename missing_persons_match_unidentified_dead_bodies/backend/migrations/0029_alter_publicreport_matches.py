# Generated by Django 4.0.8 on 2023-02-04 11:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0028_publicreport_missing_or_found'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publicreport',
            name='matches',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.report'),
        ),
    ]