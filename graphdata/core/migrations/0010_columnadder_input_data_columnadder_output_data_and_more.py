# Generated by Django 5.1.4 on 2024-12-20 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_remove_columnadder_type_remove_csvimporter_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='columnadder',
            name='input_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='columnadder',
            name='output_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='csvimporter',
            name='input_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='csvimporter',
            name='output_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='duplicator',
            name='input_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='duplicator',
            name='output_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='exporter',
            name='input_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='exporter',
            name='output_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='filterer',
            name='input_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='filterer',
            name='output_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='joiner',
            name='input_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='joiner',
            name='output_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='regeximporter',
            name='input_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='regeximporter',
            name='output_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='selector',
            name='input_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='selector',
            name='output_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='sorter',
            name='input_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='sorter',
            name='output_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='viewer',
            name='input_data',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='viewer',
            name='output_data',
            field=models.JSONField(default=dict),
        ),
    ]
