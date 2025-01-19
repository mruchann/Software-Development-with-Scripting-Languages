# Generated by Django 5.1.4 on 2024-12-18 11:57

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_csvimporternode_delete_node'),
    ]

    operations = [
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('Csv_Importer', 'Csv_Importer'), ('Column_Adder', 'Column_Adder'), ('Duplicator', 'Duplicator'), ('Exporter', 'Exporter'), ('Filterer', 'Filterer'), ('Joiner', 'Joiner'), ('Regex_Importer', 'Regex_Importer'), ('Selector', 'Selector'), ('Sorter', 'Sorter'), ('Viewer', 'Viewer')], max_length=100)),
                ('inputs', models.JSONField(default=dict)),
                ('outputs', models.JSONField(default=dict)),
                ('params', models.JSONField(default=dict)),
                ('x', models.IntegerField()),
                ('y', models.IntegerField()),
                ('associated_graph', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.graph')),
            ],
        ),
        migrations.DeleteModel(
            name='CsvImporterNode',
        ),
    ]
