# from django.contrib.postgres.operations import CreateExtension

from django.db import migrations


def create_extension(apps, schema_editor):
    # Use the schema_editor to create the extension
    schema_editor.execute("CREATE EXTENSION IF NOT EXISTS postgis")


class Migration(migrations.Migration):
    dependencies = []
    operations = [
        migrations.RunPython(create_extension),
    ]
