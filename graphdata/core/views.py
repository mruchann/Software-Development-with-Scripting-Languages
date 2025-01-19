import json
from random import random

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required

from .forms import *
from django.forms.models import model_to_dict

from .models import *

import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_image

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def generate_random_color():
    """Generates a random hex color."""
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


def home(request):
    return render(request, 'main_page.html')


# redirected to LOGIN_URL in settings.py if not logged in
@login_required
def graphs(request):
    user = request.user
    attached_graphs = []
    detached_graphs = []
    for graph in Graph.objects.all():
        if user in graph.user_set.all():
            attached_graphs.append({
                "name": str(graph),
                "id": graph.id,
            })
        else:
            detached_graphs.append({
                "name": str(graph),
                "id": graph.id,
            })

    context = {
        'attached_graphs': attached_graphs,
        'detached_graphs': detached_graphs,
    }
    return render(request, 'graphs.html', context)


@login_required
def attach_graph(request, graph_id):
    user = request.user
    graph = Graph.objects.get(id=graph_id)
    user.attached_graphs.add(graph)
    return redirect('graphs')


@login_required
def detach_graph(request, graph_id):
    user = request.user
    graph = Graph.objects.get(id=graph_id)
    user.attached_graphs.remove(graph)
    return redirect('graphs')


@login_required
def view_graph(request, graph_id):

    user = request.user
    graph = Graph.objects.get(id=graph_id)

    if not user.attached_graphs.filter(id=graph_id).exists():
        return redirect('graphs')

    nodes = chain(
        graph.csvimporter_set.all(),
        graph.sorter_set.all(),
        graph.selector_set.all(),
        graph.filterer_set.all(),
        graph.duplicator_set.all(),
        graph.joiner_set.all(),
        graph.exporter_set.all(),
        graph.viewer_set.all(),
        graph.columnadder_set.all(),
        graph.regeximporter_set.all(),
        graph.chart_set.all(),
    )

    # Convert nodes to dict and handle UUID serialization
    serialized_nodes = []
    for node in nodes:
        node_dict = model_to_dict(node)

        # Convert UUID fields (if any) to string
        for key, value in node_dict.items():
            if isinstance(value, uuid.UUID):
                node_dict[key] = str(value)

        node_dict['color'] = generate_random_color()
        node_dict['type'] = node.type
        node_dict['id'] = str(node.id)
        node_dict['associated_graph'] = str(node.associated_graph.id)

        serialized_nodes.append(node_dict)

    context = {
        'graph_id': graph.id,
        'graph': graph,
        'nodes': json.dumps(serialized_nodes),
    }

    return render(request, 'view_graph.html', context)


def create_svg_chart(table_data):
    df = pd.DataFrame(table_data, columns=table_data[0].keys())

    header_height = 40
    row_height = 30
    margin_space = 50

    dynamic_height = margin_space + header_height + len(df) * row_height

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(df.columns),
            fill_color='paleturquoise',
            align='center',
            font=dict(size=20, color='black'),
            height = header_height
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            fill_color='lavender',
            align='left',
            font=dict(size=18, color='black'),
            height=row_height
        )
    )])

    fig.update_layout(
        autosize=True,
        width=1200,  # Adjust as needed
        height=dynamic_height,  # Adjust to fit all rows
        margin=dict(l=10, r=10, t=10, b=10)  # Set optimal margins
    )

    svg_data = to_image(fig, format='svg')  # Requires `kaleido` library

    return svg_data.decode('utf-8')

@login_required
def chart_table(request, graph_id, node_id):
    user = request.user
    graph = Graph.objects.get(id=graph_id)

    if not user.attached_graphs.filter(id=graph_id).exists():
        return redirect('graphs')

    node = graph.get_node(node_id)

    if node.input_port == "" or node.output_data[node.input_port] == []:
        messages.error(request, 'Chart is not connected to a data flow.')
        return redirect('view_graph', graph_id=graph_id)

    svg_data = create_svg_chart(node.output_data[node.input_port])

    context = {
        'svg_chart': svg_data,
        'graph_id': graph_id,
        'node_id': node_id
    }

    print(node)
    print(node.output_data)
    return render(request, 'chart.html', context)


@login_required
def viewer_table(request, graph_id, node_id):
    user = request.user
    graph = Graph.objects.get(id=graph_id)

    if not user.attached_graphs.filter(id=graph_id).exists():
        return redirect('graphs')

    node = graph.get_node(node_id)

    if node.input_port == "" or node.output_data[node.input_port] == []:
        messages.error(request, 'Viewer is not connected to a data flow.')
        return redirect('view_graph', graph_id=graph_id)

    context = {
        "data": node.output_data[node.input_port],
        "graph_id": graph_id,
        "node_id": node_id
    }

    print(node)
    print(node.output_data)
    return render(request, 'table.html', context)


@login_required
def delete_graph(request, graph_id):
    user = request.user
    graph = Graph.objects.get(id=graph_id)

    if not user.attached_graphs.filter(id=graph_id).exists():
        return redirect('graphs')

    graph.delete()
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "list_graphs",
        {
            "type": "handle_command",
            "command": "delete_graph",
            "name": str(graph),
            "id": str(graph_id),
        }
    )
    async_to_sync(channel_layer.group_send)(
        str(graph_id),
        {
            "type": "handle_command",
            "command": "delete_graph",
        }
    )

    return redirect('graphs')


@login_required
def create_graph(request):
    if request.method == 'POST':
        form = GraphCreationForm(request.POST)
        if form.is_valid():
            graph = form.save(commit=True)

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "list_graphs",
                {
                    "type": "handle_command",
                    "command": "create_graph",
                    "name": str(graph),
                    "id": str(graph.id),
                }
            )

            messages.success(request, 'Graph successfully created.')
            return redirect('graphs')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = GraphCreationForm()

    return render(request, 'create_graph.html', {'form': form})


def base_create_node(request, graph_id, creation_form, title):
    user = request.user
    graph = Graph.objects.get(id=graph_id)

    if not user.attached_graphs.filter(id=graph_id).exists():
        return redirect('graphs')

    if request.method == 'POST':
        form = creation_form(request.POST)
        if form.is_valid():
            node = form.save(commit=False)

            if not (0 <= node.x < graph.width and 0 <= node.y < graph.height):
                messages.error(request, 'Node is not within the graph\'s boundaries.')
                return redirect('view_graph', graph_id=graph_id)

            node.associated_graph = graph
            node.save()

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                str(node.associated_graph.id),
                {
                    "type": "handle_command",
                    "command": "compute",
                    "node_id": str(node.id),
                    "notif": f"{node} was created.\n",
                }
            )

            messages.success(request, 'Node successfully created.')
            return redirect('view_graph', graph_id=graph_id)
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = creation_form()

    context = {
        'form': form,
        'title': title,
    }

    return render(request, 'node_creation.html', context)


@login_required
def update_node(request, graph_id):
    user = request.user
    graph = Graph.objects.get(id=graph_id)

    if not user.attached_graphs.filter(id=graph_id).exists():
        return redirect('graphs')

    connect_form = NodeConnectForm(graph=graph)
    disconnect_form = NodeDisconnectForm(graph=graph)
    delete_form = NodeDeletionForm(graph=graph)
    field_update_form = NodeUpdateForm(graph=graph)

    if request.method == 'POST':
        if 'submit_field_update_form' in request.POST:
            field_update_form = NodeUpdateForm(request.POST)
            if field_update_form.is_valid():
                node_id = field_update_form.data['node_id']
                x = field_update_form.data['x']
                y = field_update_form.data['y']
                node = graph.get_node(node_id)
                notif = ""

                if x != "":
                    notif += f"{node}\'s x coordinate changed from {node.x} to {x}\n"
                    node.x = int(x)
                if y != "":
                    notif += f"{node}\'s y coordinate changed from {node.y} to {y}\n"
                    node.y = int(y)

                if node.type == "CsvImporter":
                    file = field_update_form.data['file']
                    if file != "":
                        notif += f"{node}\'s file changed from {node.file} to {file}\n"
                        node.file = file

                elif node.type == "Sorter":
                    sort_column = field_update_form.data['sort_column']
                    if sort_column != "":
                        notif += f"{node}\'s sort_column changed from {node.sort_column} to {sort_column}\n"
                        node.sort_column = sort_column

                elif node.type == "Selector":
                    select_columns = field_update_form.data['select_columns']
                    if select_columns != "":
                        notif += f"{node}\'s select_columns changed from {node.select_columns} to {select_columns}\n"
                        node.select_columns = select_columns

                elif node.type == "Filterer":
                    expr = field_update_form.data['expr']
                    if expr != "":
                        notif += f"{node}\'s expr changed from {node.expr} to {expr}\n"
                        node.expr = expr

                elif node.type == "Duplicator":
                    pass

                elif node.type == "Joiner":
                    join_column = field_update_form.data['join_column']
                    if join_column != "":
                        notif += f"{node}\'s join_column changed from {node.join_column} to {join_column}\n"
                        node.join_column = join_column

                elif node.type == "Exporter":
                    file = field_update_form.data['file']
                    if file != "":
                        notif += f"{node}\'s file changed from {node.file} to {file}\n"
                        node.file = file

                elif node.type == "Viewer":
                    pass

                elif node.type == "Chart":
                    pass

                elif node.type == "ColumnAdder":
                    expr = field_update_form.data['expr']
                    if expr != "":
                        notif += f"{node}\'s expr changed from {node.expr} to {expr}\n"
                        node.expr = expr

                elif node.type == "RegexImporter":
                    regex = field_update_form.data['regex']
                    columns = field_update_form.data['columns']
                    if regex != "":
                        notif += f"{node}\'s regex changed from {node.regex} to {regex}\n"
                        node.regex = regex
                    if columns != "":
                        notif += f"{node}\'s columns changed from {node.columns} to {columns}\n"
                        node.columns = columns

                node.save()

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    str(node.associated_graph.id),
                    {
                        "type": "handle_command",
                        "command": "compute",
                        "node_id": str(node.id),
                        "notif": notif,
                    }
                )

                messages.success(request, 'Node successfully updated.')
                return redirect('view_graph', graph_id=graph_id)
            else:
                messages.error(request, 'Please correct the errors in the connect form.')

        elif 'submit_connect_form' in request.POST:
            connect_form = NodeConnectForm(request.POST)
            if connect_form.is_valid():
                output_node_id = connect_form.data['output_node']
                output_port = connect_form.data['output_port']
                input_node_id = connect_form.data['input_node']
                input_port = connect_form.data['input_port']

                output_node = graph.get_node(output_node_id)
                input_node = graph.get_node(input_node_id)

                ok = graph.connect(input_node, input_port, output_node, output_port)
                graph.save()

                if not ok:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        str(output_node.associated_graph.id),
                        {
                            "type": "handle_command",
                            "command": "compute",
                            "node_id": str(output_node.id),
                            "notif": f'Could not connect {output_node} to {input_node}.\n',
                        }
                    )
                    messages.error(request, f'Could not connect {output_node} to {input_node}.')
                    return redirect('view_graph', graph_id=graph_id)

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    str(output_node.associated_graph.id),
                    {
                        "type": "handle_command",
                        "command": "compute",
                        "node_id": str(output_node.id),
                        "notif": f"{output_node}:{output_port} and {input_node}:{input_port} was connected.\n",
                    }
                )

                messages.success(request, 'Node successfully connected.')
                return redirect('view_graph', graph_id=graph_id)
            else:
                messages.error(request, 'Please correct the errors in the connect form.')

        elif 'submit_disconnect_form' in request.POST:
            disconnect_form = NodeDisconnectForm(request.POST)
            if disconnect_form.is_valid():
                output_node_id = disconnect_form.data['output_node']
                output_port = disconnect_form.data['output_port']
                input_node_id = disconnect_form.data['input_node']
                input_port = disconnect_form.data['input_port']

                output_node = graph.get_node(output_node_id)
                input_node = graph.get_node(input_node_id)

                ok = graph.disconnect(input_node, input_port, output_node, output_port)
                graph.save()

                if not ok:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        str(output_node.associated_graph.id),
                        {
                            "type": "handle_command",
                            "command": "compute",
                            "node_id": str(output_node.id),
                            "notif": f'Could not disconnect {output_node} and {input_node}.\n',
                        }
                    )
                    messages.error(request, f'Could not disconnect {output_node} and {input_node}.')
                    return redirect('view_graph', graph_id=graph_id)

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    str(output_node.associated_graph.id),
                    {
                        "type": "handle_command",
                        "command": "compute",
                        "node_id": str(output_node.id),
                    }
                )
                async_to_sync(channel_layer.group_send)(
                    str(input_node.associated_graph.id),
                    {
                        "type": "handle_command",
                        "command": "compute",
                        "node_id": str(input_node.id),
                        "notif": f"{output_node}:{output_port} and {input_node}:{input_port} was disconnected.\n",
                    }
                )

                messages.success(request, 'Node successfully disconnected.')
                return redirect('view_graph', graph_id=graph_id)
            else:
                messages.error(request, 'Please correct the errors in the disconnect form.')

        elif 'submit_delete_form' in request.POST:
            delete_form = NodeDeletionForm(request.POST)
            if delete_form.is_valid():
                node_id = delete_form.data['node']
                node = graph.get_node(node_id)

                node_inputs = copy.deepcopy(node.inputs)
                node_outputs = copy.deepcopy(node.outputs)

                affected_nodes_from_deletion = []

                for k, v in node_inputs.items():
                    # v always has 1 key value pair
                    output_port, output_node_id = next(iter(v.items()))
                    output_node = graph.get_node(output_node_id)
                    graph.disconnect(node, k, output_node, output_port)
                    affected_nodes_from_deletion.append(str(output_node_id))

                for k, v in node_outputs.items():
                    input_port, input_node_id = next(iter(v.items()))
                    input_node = graph.get_node(input_node_id)
                    graph.disconnect(input_node, input_port, node, k)
                    affected_nodes_from_deletion.append(str(input_node_id))

                node.delete()
                graph.save()

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    str(graph.id),
                    {
                        "type": "handle_command",
                        "command": "delete_node",
                        "node_id": str(node_id),
                        "notif": f"{node} was deleted.\n",
                        "affected_nodes_from_deletion": affected_nodes_from_deletion,
                    }
                )

                messages.success(request, 'Node successfully deleted.')
                return redirect('view_graph', graph_id=graph_id)
            else:
                messages.error(request, 'Please correct the errors in the delete form.')

    context = {
        'field_update_form': field_update_form,
        'connect_form': connect_form,
        'disconnect_form': disconnect_form,
        'delete_form': delete_form,
    }

    return render(request, 'node_update.html', context)


@login_required
def delete_node(request, graph_id):
    user = request.user
    graph = Graph.objects.get(id=graph_id)

    if not user.attached_graphs.filter(id=graph_id).exists():
        return redirect('graphs')

    if request.method == 'POST':
        form = NodeDeletionForm(request.POST)
        if form.is_valid():
            node_id = form.data['node']
            graph.get_node(node_id).delete()
            messages.success(request, 'Node successfully created.')
            return redirect('view_graph', graph_id=graph_id)
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = NodeDeletionForm(graph=graph)

    context = {
        'form': form,
        'title': "Delete a Node",
    }

    return render(request, 'node_deletion.html', context)


@login_required
def connect_nodes(request, graph_id):
    user = request.user
    graph = Graph.objects.get(id=graph_id)

    if not user.attached_graphs.filter(id=graph_id).exists():
        return redirect('graphs')

    if request.method == 'POST':
        form = NodeConnectForm(request.POST)
        if form.is_valid():
            output_node_id = form.data['output_node']
            output_port = form.data['output_port']
            input_node_id = form.data['input_node']
            input_port = form.data['input_port']

            output_node = graph.get_node(output_node_id)
            input_node = graph.get_node(input_node_id)

            graph.connect(input_node, input_port, output_node, output_port)

            input_node.save()
            output_node.save()
            graph.save()

            messages.success(request, 'Node successfully created.')
            return redirect('view_graph', graph_id=graph_id)
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = NodeConnectForm(graph=graph)

    context = {
        'form': form,
        'title': "Connect two nodes",
    }

    return render(request, 'node_connect.html', context)


@login_required
def disconnect_nodes(request, graph_id):
    user = request.user
    graph = Graph.objects.get(id=graph_id)

    if not user.attached_graphs.filter(id=graph_id).exists():
        return redirect('graphs')

    if request.method == 'POST':
        form = NodeDisconnectForm(request.POST)
        if form.is_valid():
            output_node_id = form.data['output_node']
            output_port = form.data['output_port']
            input_node_id = form.data['input_node']
            input_port = form.data['input_port']

            output_node = graph.get_node(output_node_id)
            input_node = graph.get_node(input_node_id)

            graph.disconnect(input_node, input_port, output_node, output_port)
            input_node.save()
            output_node.save()
            graph.save()

            messages.success(request, 'Node successfully created.')
            return redirect('view_graph', graph_id=graph_id)
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = NodeDisconnectForm(graph=graph)

    context = {
        'form': form,
        'title': "Disconnect two nodes",
    }

    return render(request, 'node_disconnect.html', context)


@login_required
def create_column_adder_node(request, graph_id):
    return base_create_node(request, graph_id, ColumnAdderCreationForm, "Create Column Adder Node")


@login_required
def create_csv_importer_node(request, graph_id):
    return base_create_node(request, graph_id, CsvImporterCreationForm, "Create CSV Importer Node")


@login_required
def create_duplicator_node(request, graph_id):
    return base_create_node(request, graph_id, DuplicatorCreationForm, "Create Duplicator Node")


@login_required
def create_exporter_node(request, graph_id):
    return base_create_node(request, graph_id, ExporterCreationForm, "Create Exporter Node")


@login_required
def create_filterer_node(request, graph_id):
    return base_create_node(request, graph_id, FiltererCreationForm, "Create Filterer Node")


@login_required
def create_joiner_node(request, graph_id):
    return base_create_node(request, graph_id, JoinerCreationForm, "Create Joiner Node")


@login_required
def create_regex_importer_node(request, graph_id):
    return base_create_node(request, graph_id, RegexImporterCreationForm, "Create RegexImporter Node")


@login_required
def create_selector_node(request, graph_id):
    return base_create_node(request, graph_id, SelectorCreationForm, "Create Selector Node")


@login_required
def create_sorter_node(request, graph_id):
    return base_create_node(request, graph_id, SorterCreationForm, "Create Sorter Node")


@login_required
def create_viewer_node(request, graph_id):
    return base_create_node(request, graph_id, ViewerCreationForm, "Create Viewer Node")

@login_required
def create_chart_node(request, graph_id):
    return base_create_node(request, graph_id, ChartCreationForm, "Create Chart Node")


class ScriptLoginView(LoginView):
    template_name = 'login.html'


class ScriptLogoutView(LogoutView):
    next_page = 'home'  # Redirect user to home page


def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            login(request, user)
            messages.success(request, "Your account has been created successfully!")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()

    return render(request, 'sign_up.html', {'form': form})


def contact(request):
    return render(request, 'contact.html')


def about(request):
    return render(request, 'about.html')

