# Generated by Django 4.0.8 on 2023-01-28 02:25

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0020_alter_raillines_isocountry'),
    ]

    operations = [
        migrations.CreateModel(
            name='MitRailLines',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('f_code', models.CharField(max_length=255, null=True)),
                ('fco', models.IntegerField()),
                ('exs', models.IntegerField()),
                ('loc', models.IntegerField()),
                ('soc', models.CharField(max_length=255, null=True)),
                ('geom', django.contrib.gis.db.models.fields.MultiLineStringField(geography=True, srid=4326)),
            ],
        ),
    ]
