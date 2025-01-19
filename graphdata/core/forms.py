from itertools import chain

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import *

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = get_user_model()
        fields = ['email', 'username', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password != password_confirm:
            raise ValidationError("Passwords do not match")

        return cleaned_data


class GraphCreationForm(forms.ModelForm):
    class Meta:
        model = Graph
        fields = '__all__'

class NodeConnectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'graph' in kwargs:
            self.graph = kwargs.pop('graph')
            super(NodeConnectForm, self).__init__(*args, **kwargs)

            viewer_choices = [(node.pk, f"Viewer: {str(node)}") for node in self.graph.viewer_set.all()]
            sorter_choices = [(node.pk, f"Sorter: {str(node)}") for node in self.graph.sorter_set.all()]
            csv_importer_choices = [(node.pk, f"Csv Importer: {str(node)}") for node in self.graph.csvimporter_set.all()]
            selector_choices = [(node.pk, f"Selector: {str(node)}") for node in self.graph.selector_set.all()]
            filterer_choices = [(node.pk, f"Filterer: {str(node)}") for node in self.graph.filterer_set.all()]
            duplicator_choices = [(node.pk, f"Duplicator: {str(node)}") for node in self.graph.duplicator_set.all()]
            joiner_choices = [(node.pk, f"Joiner: {str(node)}") for node in self.graph.joiner_set.all()]
            exporter_choices = [(node.pk, f"Exporter: {str(node)}") for node in self.graph.exporter_set.all()]
            column_adder_choices = [(node.pk, f"Column Adder: {str(node)}") for node in self.graph.columnadder_set.all()]
            regex_importer_choices = [(node.pk, f"Regex Importer: {str(node)}") for node in self.graph.regeximporter_set.all()]
            chart_choices = [(node.pk, f"Chart: {str(node)}") for node in self.graph.chart_set.all()]

            grouped_choices = [
                ('Viewers', viewer_choices),
                ('Sorters', sorter_choices),
                ('CSV Importers', csv_importer_choices),
                ('Selectors', selector_choices),
                ('Filterers', filterer_choices),
                ('Duplicators', duplicator_choices),
                ('Joiners', joiner_choices),
                ('Exporters', exporter_choices),
                ('Column Adders', column_adder_choices),
                ('Regex Importers', regex_importer_choices),
                ('Charts', chart_choices),
            ]

            self.fields['output_node'] = forms.ChoiceField(
                choices=grouped_choices,
                label="Output node to connect",
                widget=forms.Select(attrs={
                    'class': 'form-control',
                })
            )
            self.fields['output_port'] = forms.CharField(max_length=255)
            self.fields['input_node'] = forms.ChoiceField(
                choices=grouped_choices,
                label="Input node to connect",
                widget=forms.Select(attrs={
                    'class': 'form-control',
                })
            )
            self.fields['input_port'] = forms.CharField(max_length=255)
        else:
            super(NodeConnectForm, self).__init__(*args, **kwargs)


class NodeDisconnectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'graph' in kwargs:
            self.graph = kwargs.pop('graph')
            super(NodeDisconnectForm, self).__init__(*args, **kwargs)

            viewer_choices = [(node.pk, f"Viewer: {str(node)}") for node in self.graph.viewer_set.all()]
            sorter_choices = [(node.pk, f"Sorter: {str(node)}") for node in self.graph.sorter_set.all()]
            csv_importer_choices = [(node.pk, f"Csv Importer: {str(node)}") for node in self.graph.csvimporter_set.all()]
            selector_choices = [(node.pk, f"Selector: {str(node)}") for node in self.graph.selector_set.all()]
            filterer_choices = [(node.pk, f"Filterer: {str(node)}") for node in self.graph.filterer_set.all()]
            duplicator_choices = [(node.pk, f"Duplicator: {str(node)}") for node in self.graph.duplicator_set.all()]
            joiner_choices = [(node.pk, f"Joiner: {str(node)}") for node in self.graph.joiner_set.all()]
            exporter_choices = [(node.pk, f"Exporter: {str(node)}") for node in self.graph.exporter_set.all()]
            column_adder_choices = [(node.pk, f"Column Adder: {str(node)}") for node in self.graph.columnadder_set.all()]
            regex_importer_choices = [(node.pk, f"Regex Importer: {str(node)}") for node in self.graph.regeximporter_set.all()]
            chart_choices = [(node.pk, f"Chart: {str(node)}") for node in self.graph.chart_set.all()]

            grouped_choices = [
                ('Viewers', viewer_choices),
                ('Sorters', sorter_choices),
                ('CSV Importers', csv_importer_choices),
                ('Selectors', selector_choices),
                ('Filterers', filterer_choices),
                ('Duplicators', duplicator_choices),
                ('Joiners', joiner_choices),
                ('Exporters', exporter_choices),
                ('Column Adders', column_adder_choices),
                ('Regex Importers', regex_importer_choices),
                ('Charts', chart_choices),
            ]

            self.fields['output_node'] = forms.ChoiceField(
                choices=grouped_choices,
                label="Output node to disconnect",
                widget=forms.Select(attrs={
                    'class': 'form-control',
                })
            )
            self.fields['output_port'] = forms.CharField(max_length=255)
            self.fields['input_node'] = forms.ChoiceField(
                choices=grouped_choices,
                label="Input node to disconnect",
                widget=forms.Select(attrs={
                    'class': 'form-control',
                })
            )
            self.fields['input_port'] = forms.CharField(max_length=255)
        else:
            super(NodeDisconnectForm, self).__init__(*args, **kwargs)


class NodeDeletionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'graph' in kwargs:
            self.graph = kwargs.pop('graph')
            super(NodeDeletionForm, self).__init__(*args, **kwargs)
            viewer_choices = [(node.pk, f"Viewer: {str(node)}") for node in self.graph.viewer_set.all()]
            sorter_choices = [(node.pk, f"Sorter: {str(node)}") for node in self.graph.sorter_set.all()]
            csv_importer_choices = [(node.pk, f"Csv Importer: {str(node)}") for node in self.graph.csvimporter_set.all()]
            selector_choices = [(node.pk, f"Selector: {str(node)}") for node in self.graph.selector_set.all()]
            filterer_choices = [(node.pk, f"Filterer: {str(node)}") for node in self.graph.filterer_set.all()]
            duplicator_choices = [(node.pk, f"Duplicator: {str(node)}") for node in self.graph.duplicator_set.all()]
            joiner_choices = [(node.pk, f"Joiner: {str(node)}") for node in self.graph.joiner_set.all()]
            exporter_choices = [(node.pk, f"Exporter: {str(node)}") for node in self.graph.exporter_set.all()]
            column_adder_choices = [(node.pk, f"Column Adder: {str(node)}") for node in self.graph.columnadder_set.all()]
            regex_importer_choices = [(node.pk, f"Regex Importer: {str(node)}") for node in self.graph.regeximporter_set.all()]
            chart_choices = [(node.pk, f"Chart: {str(node)}") for node in self.graph.chart_set.all()]

            grouped_choices = [
                ('Viewers', viewer_choices),
                ('Sorters', sorter_choices),
                ('CSV Importers', csv_importer_choices),
                ('Selectors', selector_choices),
                ('Filterers', filterer_choices),
                ('Duplicators', duplicator_choices),
                ('Joiners', joiner_choices),
                ('Exporters', exporter_choices),
                ('Column Adders', column_adder_choices),
                ('Regex Importers', regex_importer_choices),
                ('Charts', chart_choices),
            ]

            self.fields['node'] = forms.ChoiceField(
                 choices=grouped_choices,
                 label="Node to delete",
                 widget=forms.Select(attrs={
                     'class': 'form-control'
                 })
            )
        else:
            super(NodeDeletionForm, self).__init__(*args, **kwargs)


class NodeUpdateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'graph' in kwargs:
            self.graph = kwargs.pop('graph')
            super(NodeUpdateForm, self).__init__(*args, **kwargs)

            viewer_choices = [(node.pk, f"Viewer: {str(node)}") for node in self.graph.viewer_set.all()]
            sorter_choices = [(node.pk, f"Sorter: {str(node)}") for node in self.graph.sorter_set.all()]
            csv_importer_choices = [(node.pk, f"Csv Importer: {str(node)}") for node in self.graph.csvimporter_set.all()]
            selector_choices = [(node.pk, f"Selector: {str(node)}") for node in self.graph.selector_set.all()]
            filterer_choices = [(node.pk, f"Filterer: {str(node)}") for node in self.graph.filterer_set.all()]
            duplicator_choices = [(node.pk, f"Duplicator: {str(node)}") for node in self.graph.duplicator_set.all()]
            joiner_choices = [(node.pk, f"Joiner: {str(node)}") for node in self.graph.joiner_set.all()]
            exporter_choices = [(node.pk, f"Exporter: {str(node)}") for node in self.graph.exporter_set.all()]
            column_adder_choices = [(node.pk, f"Column Adder: {str(node)}") for node in self.graph.columnadder_set.all()]
            regex_importer_choices = [(node.pk, f"Regex Importer: {str(node)}") for node in self.graph.regeximporter_set.all()]
            chart_choices = [(node.pk, f"Chart: {str(node)}") for node in self.graph.chart_set.all()]

            grouped_choices = [
                ('Viewers', viewer_choices),
                ('Sorters', sorter_choices),
                ('CSV Importers', csv_importer_choices),
                ('Selectors', selector_choices),
                ('Filterers', filterer_choices),
                ('Duplicators', duplicator_choices),
                ('Joiners', joiner_choices),
                ('Exporters', exporter_choices),
                ('Column Adders', column_adder_choices),
                ('Regex Importers', regex_importer_choices),
                ('Charts', chart_choices),
            ]

            self.fields['node_id'] = forms.ChoiceField(
                choices=grouped_choices,
                label="Node to be updated",
                widget=forms.Select(attrs={
                    'class': 'form-control',
                })
            )
            self.fields['x'] = forms.CharField(max_length=255)
            self.fields['x'].required = False
            self.fields['y'] = forms.CharField(max_length=255)
            self.fields['y'].required = False
            self.fields['file'] = forms.CharField(max_length=255)
            self.fields['file'].required = False
            self.fields['sort_column'] = forms.CharField(max_length=255)
            self.fields['sort_column'].required = False
            self.fields['select_columns'] = forms.CharField(max_length=255)
            self.fields['select_columns'].required = False
            self.fields['expr'] = forms.CharField(max_length=255)
            self.fields['expr'].required = False
            self.fields['join_column'] = forms.CharField(max_length=255)
            self.fields['join_column'].required = False
            self.fields['regex'] = forms.CharField(max_length=255)
            self.fields['regex'].required = False
            self.fields['columns'] = forms.CharField(max_length=255)
            self.fields['columns'].required = False
        else:
            super(NodeUpdateForm, self).__init__(*args, **kwargs)


class ColumnAdderCreationForm(forms.ModelForm):
    class Meta:
        model = ColumnAdder
        exclude = ('associated_graph', 'inputs', 'outputs', 'params', 'input_data', 'output_data', 'input_port', 'output_port')


class CsvImporterCreationForm(forms.ModelForm):
    class Meta:
        model = CsvImporter
        exclude = ('associated_graph', 'inputs', 'outputs', 'params', 'input_data', 'output_data', 'output_port', 'file_updated_timestamp')


class DuplicatorCreationForm(forms.ModelForm):
    class Meta:
        model = Duplicator
        exclude = ('associated_graph', 'inputs', 'outputs', 'params', 'input_data', 'output_data', 'input_port', 'output_port1', 'output_port2')


class ExporterCreationForm(forms.ModelForm):
    class Meta:
        model = Exporter
        exclude = ('associated_graph', 'inputs', 'outputs', 'params', 'input_data', 'output_data', 'input_port')


class FiltererCreationForm(forms.ModelForm):
    class Meta:
        model = Filterer
        exclude = ('associated_graph', 'inputs', 'outputs', 'params', 'input_data', 'output_data', 'input_port', 'output_port')


class JoinerCreationForm(forms.ModelForm):
    class Meta:
        model = Joiner
        exclude = ('associated_graph', 'inputs', 'outputs', 'params', 'input_data', 'output_data', 'input_port1', 'input_port2', 'output_port')


class RegexImporterCreationForm(forms.ModelForm):
    class Meta:
        model = RegexImporter
        exclude = ('associated_graph', 'inputs', 'outputs', 'params', 'input_data', 'output_data', 'output_port')


class SelectorCreationForm(forms.ModelForm):
    class Meta:
        model = Selector
        exclude = ('associated_graph', 'inputs', 'outputs', 'params', 'input_data', 'output_data', 'input_port', 'output_port')


class SorterCreationForm(forms.ModelForm):
    class Meta:
        model = Sorter
        exclude = ('associated_graph', 'inputs', 'outputs', 'params', 'input_data', 'output_data', 'input_port', 'output_port')


class ViewerCreationForm(forms.ModelForm):
    class Meta:
        model = Viewer
        exclude = ('associated_graph', 'inputs', 'outputs', 'params', 'input_data', 'output_data', 'input_port')

class ChartCreationForm(forms.ModelForm):
    class Meta:
        model = Chart
        exclude = ('associated_graph', 'inputs', 'outputs', 'params', 'input_data', 'output_data', 'input_port')

