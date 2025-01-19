import random
import re
from uuid import uuid4
from django.db import models
from django.contrib.auth.models import AbstractUser
from threading import *
import copy
import csv
import uuid
import os


def save_after(func):
    def wrapper(self, *args, **kwargs):
        # Call the original method
        result = func(self, *args, **kwargs)
        # Save the model instance
        self.save()
        return result
    return wrapper


class Monitor:
    def __init__(self):
        self.lock = RLock()

    @classmethod
    def sync(cls, method):
        def w(self, *args, **kwargs):
            with self.lock:
                return method(self, *args, **kwargs)
        return w

    def CV(self):
        return Condition(self.lock)


class Graph(models.Model, Monitor):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)
    width = models.IntegerField()
    height = models.IntegerField()

    def __str__(self):
        return f"{self.name} ({self.width}x{self.height})"

    @Monitor.sync
    @save_after
    def connect(self, input_node, input_port_name: str, output_node, output_port_name: str):
        try:
            input_node.add_input_port_name(input_port_name)
            output_node.add_output_port_name(output_port_name)
        except:
            try:
                input_node.remove_input_port_name(input_port_name)
            except:
                pass
            try:
                output_node.remove_output_port_name(output_port_name)
            except:
                pass
            return False

        if input_port_name not in input_node.inputs:
            input_node.inputs[input_port_name] = dict()
        input_node.inputs[input_port_name][output_port_name] = str(output_node.id)

        if output_port_name not in output_node.outputs:
            output_node.outputs[output_port_name] = dict()
        output_node.outputs[output_port_name][input_port_name] = str(input_node.id)

        input_node.save()
        output_node.save()
        return True

    @Monitor.sync
    def disconnect(self, input_node, input_port_name: str, output_node, output_port_name: str):
        try:
            input_node.remove_input_port_name(input_port_name)
            output_node.remove_output_port_name(output_port_name)
        except:
            try:
                input_node.add_input_port_name(input_port_name)
            except:
                pass
            try:
                output_node.add_output_port_name(output_port_name)
            except:
                pass
            return False
        input_node.inputs.pop(input_port_name)
        output_node.outputs.pop(output_port_name)

        input_node.input_data.pop(input_port_name, None)
        output_node.output_data.pop(output_port_name, None)

        input_node.save()
        output_node.save()
        return True

    @Monitor.sync
    def pick(self, x, y):
        for node in self.get_all_nodes:
            if node.x == x and node.y == y:
                return node.id
        return None

    @Monitor.sync
    def select(self, x: float, y: float, w: float, h: float):
        selected_nodes = []
        for node in self.get_all_nodes:
            if x <= node.x <= x + w and y <= node.y <= y + h:
                selected_nodes.append(node.id)
        return selected_nodes

    @Monitor.sync
    def get_all_nodes(self):
        all_nodes = []
        for csvimporter in self.csvimporter_set.all():
            all_nodes.append(csvimporter)
        for sorter in self.sorter_set.all():
            all_nodes.append(sorter)
        for selector in self.selector_set.all():
            all_nodes.append(selector)
        for filterer in self.filterer_set.all():
            all_nodes.append(filterer)
        for duplicator in self.duplicator_set.all():
            all_nodes.append(duplicator)
        for joiner in self.joiner_set.all():
            all_nodes.append(joiner)
        for exporter in self.exporter_set.all():
            all_nodes.append(exporter)
        for viewer in self.viewer_set.all():
            all_nodes.append(viewer)
        for columnadder in self.columnadder_set.all():
            all_nodes.append(columnadder)
        for regeximporter in self.regeximporter_set.all():
            all_nodes.append(regeximporter)
        for chart in self.chart_set.all():
            all_nodes.append(chart)
        return all_nodes

    @Monitor.sync
    def get_node(self, node_id):
        if isinstance(node_id, str):
            node_id = uuid.UUID(node_id)
        for csvimporter in self.csvimporter_set.all():
            if csvimporter.id == node_id:
                return csvimporter
        for sorter in self.sorter_set.all():
            if sorter.id == node_id:
                return sorter
        for selector in self.selector_set.all():
            if selector.id == node_id:
                return selector
        for filterer in self.filterer_set.all():
            if filterer.id == node_id:
                return filterer
        for duplicator in self.duplicator_set.all():
            if duplicator.id == node_id:
                return duplicator
        for joiner in self.joiner_set.all():
            if joiner.id == node_id:
                return joiner
        for exporter in self.exporter_set.all():
            if exporter.id == node_id:
                return exporter
        for viewer in self.viewer_set.all():
            if viewer.id == node_id:
                return viewer
        for columnadder in self.columnadder_set.all():
            if columnadder.id == node_id:
                return columnadder
        for regeximporter in self.regeximporter_set.all():
            if regeximporter.id == node_id:
                return regeximporter
        for chart in self.chart_set.all():
            if chart.id == node_id:
                return chart
        return None

    @Monitor.sync
    @save_after
    def bfs_from_node(self, node):
        q = [node]
        visited = set()

        while len(q) > 0:
            current_node = q.pop(0)
            if current_node in visited:
                continue
            visited.add(current_node)
            current_node.compute()  # compute current node's output
            print("current node", current_node)

            for output_port_name, to_node_dict in current_node.outputs.items():
                for to_node_input_port, to_node_id in to_node_dict.items():
                    to_node = self.get_node(to_node_id)
                    to_node.input_data[to_node_input_port] = copy.deepcopy(current_node.output_data[output_port_name])  # assign to_node's input to current node's output
                    to_node.save()
                    q.append(to_node)

        return visited

    @Monitor.sync
    @save_after
    def compute(self):
        q = []
        visited = set()
        for node in self.get_all_nodes():
            if node.type == "CsvImporter" or node.type == "RegexImporter":
                q.append(node)
        # print("in compute", len(q))
        while len(q) > 0:
            current_node = q.pop(0)
            if current_node in visited:
                continue
            visited.add(current_node)
            current_node.compute()  # compute current node's output

            for output_port_name, to_node_dict in current_node.outputs.items():
                for to_node_input_port, to_node_id in to_node_dict.items():
                    to_node = self.get_node(to_node_id)
                    to_node.input_data[to_node_input_port] = copy.deepcopy(current_node.output_data[output_port_name])  # assign to_node's input to current node's output
                    q.append(to_node)
                    # print(current_node.type, current_node.output_data[output_port_name])
                    # print(to_node.type, to_node.input_data[to_node_input_port])
        return visited

class Node(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    inputs = models.JSONField(default=dict)
    outputs = models.JSONField(default=dict)
    params = models.JSONField(default=dict)

    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)

    # one to many relationship (one graph to many nodes)
    # Graph will have .sorter_set, .joiner_set etc. member variables
    associated_graph = models.ForeignKey(Graph, on_delete=models.CASCADE)
    x = models.IntegerField()
    y = models.IntegerField()

    class Meta:
        abstract = True

    @property
    def color(self):
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))


class CsvImporter(Node):
    output_port = models.CharField(max_length=255, default='')
    file = models.CharField(max_length=255, default='')
    file_updated_timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CSV Importer ({self.x}, {self.y}) in {self.associated_graph}"

    @property
    def type(self) -> str:
        return "CsvImporter"

    @property
    def desc(self) -> str:
        return "An importer node with a CSV file as a parameter and has an output port for the imported data. First row of CSV file is assumed to contain column names."

    @save_after
    def add_input_port_name(self, name: str):
        raise AttributeError("CSVImporter doesn't have any input ports.")

    @save_after
    def add_output_port_name(self, name: str):
        if self.output_port != "":
            raise AttributeError("CSVImporter takes only one output port.")
        self.output_port = name

    @save_after
    def remove_input_port_name(self, name: str):
        raise AttributeError("CSVImporter doesn't have any input ports.")

    @save_after
    def remove_output_port_name(self, name: str):
        if self.output_port == "":
            raise AttributeError("CSVImporter already doesn't have an output port.")
        if self.output_port != name:
            raise AttributeError(f"CSVImporter doesn't have an output port called {name}.")
        self.output_data[name] = []
        self.output_port = ""

    @save_after
    def compute(self):
        if self.output_port == "":
            return

        if self.file == "":
            self.output_data[self.output_port] = []
            return

        file_modification_timestamp = os.path.getmtime(self.file)

        self.file_updated_timestamp = file_modification_timestamp
        self.output_data[self.output_port] = []
        with open(self.file, "r") as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                new_row = dict()
                for k, v in row.items():
                    try:
                        v = int(v)
                    except ValueError:
                        try:
                            v = float(v)
                        except ValueError:
                            pass
                    new_row[k] = v
                self.output_data[self.output_port].append(new_row)

class Sorter(Node):
    input_port = models.CharField(max_length=255, default='')
    output_port = models.CharField(max_length=255, default='')
    sort_column = models.CharField(max_length=255, default='')

    def __str__(self):
        return f"Sorter ({self.x}, {self.y}) in {self.associated_graph}"

    @property
    def type(self) -> str:
        return "Sorter"

    @save_after
    def compute(self):
        if self.output_port == "":
            return

        if self.input_port == "":
            self.output_data[self.output_port] = []
            return

        if len(self.input_data[self.input_port]) == 0:
            self.output_data[self.output_port] = []
            return

        output_data = copy.deepcopy(self.input_data[self.input_port])
        output_data.sort(key=lambda x: x[self.sort_column])
        self.output_data[self.output_port] = output_data

    @save_after
    def add_input_port_name(self, name: str):
        if self.input_port != "":
            raise AttributeError("Sorter takes only one input port.")
        self.input_port = name

    @save_after
    def add_output_port_name(self, name: str):
        if self.output_port != "":
            raise AttributeError("Sorter takes only one output port.")
        self.output_port = name

    @save_after
    def remove_input_port_name(self, name: str):
        if self.input_port == "":
            raise AttributeError("Sorter currently doesn't have an input port.")
        if self.input_port != name:
            raise AttributeError(f"Sorter doesn't have an input port called {name}.")
        self.input_data[name] = []
        self.input_port = ""

    @save_after
    def remove_output_port_name(self, name: str):
        if self.output_port == "":
            raise AttributeError("Sorter currently doesn't have an output port.")
        if self.output_port != name:
            raise AttributeError(f"Sorter doesn't have an output port called {name}.")
        self.output_data[name] = []
        self.output_port = ""

class Selector(Node):
    input_port = models.CharField(max_length=255, default='')
    output_port = models.CharField(max_length=255, default='')
    select_columns = models.CharField(max_length=255, default='')

    def __str__(self):
        return f"Selector ({self.x}, {self.y}) in {self.associated_graph}"

    @property
    def type(self) -> str:
        return "Selector"

    @save_after
    def compute(self):
        if self.output_port == "":
            return

        if self.input_port == "":
            self.output_data[self.output_port] = []
            return

        if len(self.input_data[self.input_port]) == 0:
            self.output_data[self.output_port] = []
            return

        select_columns = self.select_columns.split(",")

        for select_column in select_columns:
            if select_column not in self.input_data[self.input_port][0]:
                raise AttributeError(f"{select_column} is not a valid column name.")

        self.output_data[self.output_port] = []
        for row in self.input_data[self.input_port]:
            selected_row = dict()
            for k, v in row.items():
                if k not in select_columns:
                    continue
                selected_row[k] = v
            self.output_data[self.output_port].append(selected_row)

    @save_after
    def add_input_port_name(self, name: str):
        if self.input_port != "":
            raise AttributeError("Selector takes only one input port.")
        self.input_port = name

    @save_after
    def add_output_port_name(self, name: str):
        if self.output_port != "":
            raise AttributeError("Selector takes only one output port.")
        self.output_port = name

    @save_after
    def remove_input_port_name(self, name: str):
        if self.input_port == "":
            raise AttributeError("Selector currently doesn't have an input port.")
        if self.input_port != name:
            raise AttributeError(f"Selector doesn't have an input port called {name}.")
        self.input_data[name] = []
        self.input_port = ""

    @save_after
    def remove_output_port_name(self, name: str):
        if self.output_port == "":
            raise AttributeError("Selector currently doesn't have an output port.")
        if self.output_port != name:
            raise AttributeError(f"Selector doesn't have an output port called {name}.")
        self.output_data[name] = []
        self.output_port = ""


class Filterer(Node):
    input_port = models.CharField(max_length=255, default='')
    output_port = models.CharField(max_length=255, default='')
    expr = models.CharField(max_length=255, default='')

    def __str__(self):
        return f"Filterer ({self.x}, {self.y}) in {self.associated_graph}"

    @property
    def type(self) -> str:
        return "Filterer"

    @save_after
    def compute(self):
        if self.output_port == "":
            return

        if self.input_port == "":
            self.output_data[self.output_port] = []
            return

        if len(self.input_data[self.input_port]) == 0:
            self.output_data[self.output_port] = []
            return

        column, symbol, number = self.expr.split(' ')
        expr = eval(f"lambda d: d['{column}'] {symbol} {number}")
        print(self.input_data)
        output_data = copy.deepcopy(self.input_data[self.input_port])
        print(output_data)
        output_data = list(filter(expr, output_data))
        print(output_data)
        self.output_data[self.output_port] = output_data

    @save_after
    def add_input_port_name(self, name: str):
        if self.input_port != "":
            raise AttributeError("Filterer takes only one input port.")
        self.input_port = name

    @save_after
    def add_output_port_name(self, name: str):
        if self.output_port != "":
            raise AttributeError("Filterer takes only one output port.")
        self.output_port = name

    @save_after
    def remove_input_port_name(self, name: str):
        if self.input_port == "":
            raise AttributeError("Filterer currently doesn't have an input port.")
        if self.input_port != name:
            raise AttributeError(f"Filterer doesn't have an input port called {name}.")
        self.input_data[name] = []
        self.input_port = ""

    @save_after
    def remove_output_port_name(self, name: str):
        if self.output_port == "":
            raise AttributeError("Filterer currently doesn't have an output port.")
        if self.output_port != name:
            raise AttributeError(f"Filterer doesn't have an output port called {name}.")
        self.output_data[name] = []
        self.output_port = ""


class Duplicator(Node):
    input_port = models.CharField(max_length=255, default='')
    output_port1 = models.CharField(max_length=255, default='')
    output_port2 = models.CharField(max_length=255, default='')

    def __str__(self):
        return f"Duplicator ({self.x}, {self.y}) in {self.associated_graph}"

    @property
    def type(self) -> str:
        return "Duplicator"

    @save_after
    def compute(self):
        if self.input_port == "":
            self.output_data[self.output_port1] = []
            self.output_data[self.output_port2] = []
            return

        if len(self.input_data[self.input_port]) == 0:
            if self.output_port1 != "":
                self.output_data[self.output_port1] = []
            if self.output_port2 != "":
                self.output_data[self.output_port2] = []
            return

        output_data_left = copy.deepcopy(self.input_data[self.input_port])
        output_data_right = copy.deepcopy(self.input_data[self.input_port])

        if self.output_port1 != "":
            self.output_data[self.output_port1] = output_data_left
        if self.output_port2 != "":
            self.output_data[self.output_port2] = output_data_right

    @save_after
    def add_input_port_name(self, name: str):
        if self.input_port != "":
            raise AttributeError("Duplicator takes only one input port.")
        self.input_port = name

    @save_after
    def add_output_port_name(self, name: str):
        if self.output_port1 == "":
            self.output_port1 = name
            return
        if self.output_port2 == "":
            self.output_port2 = name
            return
        raise AttributeError("Duplicator takes two output ports.")

    @save_after
    def remove_input_port_name(self, name: str):
        if self.input_port == "":
            raise AttributeError("Duplicator currently doesn't have an input port.")
        if self.input_port != name:
            raise AttributeError(f"Duplicator doesn't have an input port called {name}.")
        self.input_data[name] = []
        self.input_port = ""

    @save_after
    def remove_output_port_name(self, name: str):
        if self.output_port1 == "" and self.output_port2 == "":
            raise AttributeError("Duplicator currently doesn't have an output port.")
        if self.output_port1 != name and self.output_port2 != name:
            raise AttributeError(f"Duplicator doesn't have an output port called {name}.")
        self.output_data[name] = []
        if self.output_port1 == name:
            self.output_port1 = ""
        if self.output_port2 == name:
            self.output_port2 = ""


class Joiner(Node):
    input_port1 = models.CharField(max_length=255, default='')
    input_port2 = models.CharField(max_length=255, default='')
    output_port = models.CharField(max_length=255, default='')
    join_column = models.CharField(max_length=255, default='')

    def __str__(self):
        return f"Joiner ({self.x}, {self.y}) in {self.associated_graph}"

    @property
    def type(self) -> str:
        return "Joiner"

    @save_after
    def compute(self):
        if self.output_port == "":
            return

        if self.input_port1 == "" or self.input_port2 == "":
            self.output_data[self.output_port] = []
            return

        if len(self.input_data[self.input_port1]) == 0 and len(self.input_data[self.input_port2]) == 0:
            self.output_data[self.output_port] = []
            return

        input1 = copy.deepcopy(self.input_data[self.input_port1])
        input2 = copy.deepcopy(self.input_data[self.input_port2])
        result = []

        if self.join_column not in input1[0] or self.join_column not in input2[0]:
            self.output_data[self.output_port] = []
            return

        i, j = 0, 0
        # print(input1)
        # print(input2)
        while i < len(input1) and j < len(input2):
            if input1[i][self.join_column] < input2[j][self.join_column]:
                i += 1
            elif input1[i][self.join_column] > input2[j][self.join_column]:
                j += 1
            else:
                result.append({**input1[i], **input2[j]})
                i += 1
                j += 1

        self.output_data[self.output_port] = result

    @save_after
    def add_input_port_name(self, name: str):
        if self.input_port1 == "":
            self.input_port1 = name
            return
        if self.input_port2 == "":
            self.input_port2 = name
            return
        raise AttributeError("Joiner takes two input ports.")

    @save_after
    def add_output_port_name(self, name: str):
        if self.output_port == "":
            self.output_port = name
            return
        raise AttributeError("Joiner takes only one output port.")

    @save_after
    def remove_input_port_name(self, name: str):
        if self.input_port1 == "" and self.input_port2 == "":
            raise AttributeError("Joiner currently doesn't have an input port.")
        if self.input_port1 != name and self.input_port2 != name:
            raise AttributeError(f"Joiner doesn't have an input port called {name}.")
        self.input_data[name] = []
        if self.input_port1 == name:
            self.input_port1 = ""
            return
        if self.input_port2 == name:
            self.input_port2 = ""
            return

    @save_after
    def remove_output_port_name(self, name: str):
        if self.output_port == "":
            raise AttributeError("Joiner currently doesn't have an output port.")
        if self.output_port != name:
            raise AttributeError(f"Joiner doesn't have an output port called {name}.")
        self.output_data[name] = []
        self.output_port = ""

class Exporter(Node):
    input_port = models.CharField(max_length=255, default='')
    file = models.CharField(max_length=255, default='')

    def __str__(self):
        return f"Exporter ({self.x}, {self.y}) in {self.associated_graph}"

    @property
    def type(self) -> str:
        return "Exporter"

    @save_after
    def compute(self):
        if self.input_port == "" or self.file == "":
            return

        with open(self.file, "w") as f:
            csv_writer = csv.DictWriter(f, fieldnames=self.input_data[self.input_port][0].keys())
            csv_writer.writeheader()
            csv_writer.writerows(self.input_data[self.input_port])

    @save_after
    def add_input_port_name(self, name: str):
        if self.input_port != "":
            raise AttributeError("Exporter takes only one input port.")
        self.input_port = name

    @save_after
    def add_output_port_name(self, name: str):
        raise AttributeError("Exporter doesn't have any output ports.")

    @save_after
    def remove_input_port_name(self, name: str):
        if self.input_port == "":
            raise AttributeError("Exporter already doesn't have an input port.")
        if self.input_port != name:
            raise AttributeError(f"Exporter doesn't have an input port called {name}.")
        self.input_data[name] = []
        self.input_port = ""

    @save_after
    def remove_output_port_name(self, name: str):
        raise AttributeError("Exporter doesn't have any output ports.")


class Viewer(Node):
    input_port = models.CharField(max_length=255, default='')

    def __str__(self):
        return f"Viewer ({self.x}, {self.y}) in {self.associated_graph}"

    @property
    def type(self) -> str:
        return "Viewer"

    @save_after
    def compute(self):
        if self.input_port == "":
            return
        if len(self.input_data[self.input_port]) == 0:
            self.output_data[self.input_port] = []
            return

        self.output_data[self.input_port] = self.input_data[self.input_port]

    @save_after
    def add_input_port_name(self, name: str):
        if self.input_port != "":
            raise AttributeError("Viewer takes only one input port.")
        self.input_port = name

    @save_after
    def add_output_port_name(self, name: str):
        raise AttributeError("Viewer can't have any output ports.")

    @save_after
    def remove_input_port_name(self, name: str):
        if self.input_port == "":
            raise AttributeError("Viewer already doesn't have an input port.")
        if self.input_port != name:
            raise AttributeError(f"Viewer doesn't have an input port called {name}.")
        self.input_data[name] = []
        self.output_data[name] = []
        self.input_port = ""

    @save_after
    def remove_output_port_name(self, name: str):
        raise AttributeError("Viewer doesn't have any output ports.")

class Chart(Node):
    input_port = models.CharField(max_length=255, default='')

    def __str__(self):
        return f"Chart ({self.x}, {self.y}) in {self.associated_graph}"

    @property
    def type(self) -> str:
        return "Chart"

    @save_after
    def compute(self):
        if self.input_port == "":
            return
        if len(self.input_data[self.input_port]) == 0:
            self.output_data[self.input_port] = []
            return

        self.output_data[self.input_port] = self.input_data[self.input_port]

    @save_after
    def add_input_port_name(self, name: str):
        if self.input_port != "":
            raise AttributeError("Chart takes only one input port.")
        self.input_port = name

    @save_after
    def add_output_port_name(self, name: str):
        raise AttributeError("Chart can't have any output ports.")

    @save_after
    def remove_input_port_name(self, name: str):
        if self.input_port == "":
            raise AttributeError("Chart already doesn't have an input port.")
        if self.input_port != name:
            raise AttributeError(f"Chart doesn't have an input port called {name}.")
        self.input_data[name] = []
        self.output_data[name] = []
        self.input_port = ""

    @save_after
    def remove_output_port_name(self, name: str):
        raise AttributeError("Chart doesn't have any output ports.")

class ColumnAdder(Node):
    input_port = models.CharField(max_length=255, default='')
    output_port = models.CharField(max_length=255, default='')
    expr = models.CharField(max_length=255, default='')

    def __str__(self):
        return f"Column Adder ({self.x}, {self.y}) in {self.associated_graph}"

    @property
    def type(self) -> str:
        return "ColumnAdder"

    @save_after
    def compute(self):
        if self.output_port == "":
            return

        if self.input_port == "":
            self.output_data[self.output_port] = []
            return

        if len(self.input_data[self.input_port]) == 0:
            self.output_data[self.output_port] = []
            return

        try:
            expr = eval(f"lambda self: {self.expr}")
            out = []
            for input_data in self.input_data[self.input_port]:
                out.append(input_data | { f"{self.expr}": expr(input_data) })
            self.output_data[self.output_port] = out
        except KeyError:
            self.output_data[self.output_port] = []

    @save_after
    def add_input_port_name(self, name: str):
        if self.input_port != "":
            raise AttributeError("ColumnAdder takes only one input port.")
        self.input_port = name

    @save_after
    def add_output_port_name(self, name: str):
        if self.output_port != "":
            raise AttributeError("ColumnAdder takes only one output port.")
        self.output_port = name

    @save_after
    def remove_input_port_name(self, name: str):
        if self.input_port == "":
            raise AttributeError("ColumnAdder currently doesn't have an input port.")
        if self.input_port != name:
            raise AttributeError(f"ColumnAdder doesn't have an input port called {name}.")
        self.input_data[name] = []
        self.input_port = ""

    @save_after
    def remove_output_port_name(self, name: str):
        if self.output_port == "":
            raise AttributeError("ColumnAdder currently doesn't have an output port.")
        if self.output_port != name:
            raise AttributeError(f"ColumnAdder doesn't have an output port called {name}.")
        self.output_data[name] = []
        self.output_port = ""


class RegexImporter(Node):
    output_port = models.CharField(max_length=255, default='')
    file = models.CharField(max_length=255, default='')
    file_updated_timestamp = models.DateTimeField(auto_now=True)
    regex = models.CharField(max_length=255, default='')
    columns = models.CharField(max_length=255, default='')

    def __str__(self):
        return f"Regex Importer ({self.x}, {self.y}) in {self.associated_graph}"

    @property
    def type(self) -> str:
        return "RegexImporter"

    @save_after
    def compute(self):
        if self.output_port == "":
            return

        if self.file == "":
            self.output_data[self.output_port] = []
            return

        file_modification_timestamp = os.path.getmtime(self.file)

        self.file_updated_timestamp = file_modification_timestamp
        self.output_data[self.output_port] = []
        cols = self.columns.split(',')
        with open(self.file, "r") as f:
            for line in f:
                matched = re.match(self.regex, line)
                if matched is None:
                    continue

                if len(matched.groups()) != len(cols):
                    continue

                new_row = dict()
                for k, v in zip(cols, matched.groups()):
                    try:
                        v = int(v)
                    except ValueError:
                        try:
                            v = float(v)
                        except ValueError:
                            pass
                    new_row[k] = v

                self.output_data[self.output_port].append(new_row)

    @save_after
    def add_input_port_name(self, name: str):
        raise AttributeError("RegExImporter doesn't have any input ports.")

    @save_after
    def add_output_port_name(self, name: str):
        if self.output_port != "":
            raise AttributeError("RegExImporter takes only one output port.")
        self.output_port = name

    @save_after
    def remove_input_port_name(self, name: str):
        raise AttributeError("RegExImporter doesn't have any input ports.")

    @save_after
    def remove_output_port_name(self, name: str):
        if self.output_port == "":
            raise AttributeError("RegExImporter already doesn't have an output port.")
        if self.output_port != name:
            raise AttributeError(f"RegExImporter doesn't have an output port called {name}.")
        self.output_data[name] = []
        self.output_port = ""



class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    # Graph will have .user_set member variable
    attached_graphs = models.ManyToManyField(Graph)

    def __str__(self):
        return f"{self.username} ({self.email})"
