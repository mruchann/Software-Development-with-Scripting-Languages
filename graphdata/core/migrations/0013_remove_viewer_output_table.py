# Generated by Django 5.1.4 on 2024-12-21 12:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_viewer_output_table'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='viewer',
            name='output_table',
        ),
    ]
