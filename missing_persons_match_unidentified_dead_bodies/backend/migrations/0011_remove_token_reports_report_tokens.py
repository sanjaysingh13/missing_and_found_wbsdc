# Generated by Django 4.0.8 on 2023-01-15 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0010_report_description_search_vector_token'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='token',
            name='reports',
        ),
        migrations.AddField(
            model_name='report',
            name='tokens',
            field=models.ManyToManyField(to='backend.token'),
        ),
    ]
