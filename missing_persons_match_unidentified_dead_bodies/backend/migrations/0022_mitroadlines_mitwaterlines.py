# Generated by Django 4.0.8 on 2023-01-28 07:42

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0021_mitraillines'),
    ]

    operations = [
        migrations.CreateModel(
            name='MitRoadLines',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('f_code', models.CharField(max_length=255, null=True)),
                ('acc', models.IntegerField()),
                ('exs', models.IntegerField()),
                ('rst', models.IntegerField()),
                ('med', models.IntegerField()),
                ('rtt', models.IntegerField()),
                ('rsu', models.IntegerField()),
                ('loc', models.IntegerField()),
                ('soc', models.CharField(max_length=255, null=True)),
                ('geom', django.contrib.gis.db.models.fields.MultiLineStringField(geography=True, srid=4326)),
            ],
        ),
        migrations.CreateModel(
            name='MitWaterLines',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('f_code', models.CharField(max_length=255, null=True)),
                ('hyc', models.IntegerField()),
                ('lit', models.IntegerField()),
                ('nam', models.CharField(max_length=255, null=True)),
                ('soc', models.CharField(max_length=255, null=True)),
                ('geom', django.contrib.gis.db.models.fields.MultiLineStringField(geography=True, srid=4326)),
            ],
        ),
    ]