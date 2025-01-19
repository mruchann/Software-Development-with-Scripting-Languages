import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import *
from .views import generate_random_color, create_svg_chart


class GraphConsumer(WebsocketConsumer):
    def connect(self):
        self.graph_id = str(self.scope["url_route"]["kwargs"]["graph_id"])
        self.graph = Graph.objects.get(id=self.graph_id)

        async_to_sync(self.channel_layer.group_add)(
            self.graph_id,
            self.channel_name,
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.graph_id,
            self.channel_name,
        )

    def handle_command(self, event):
        print("IN HANDLE COMMAND? <Graph>")
        command = event.get("command", None)
        node_id = event.get("node_id", None)
        notif = event.get("notif", "")
        affected_nodes_from_deletion = event.get("affected_nodes_from_deletion", None)

        if command == "compute":
            node = self.graph.get_node(node_id)
            visited = self.graph.bfs_from_node(node)
            affected_nodes = []
            for node in visited:
                affected_nodes.append({
                    "id": str(node.id),
                    "x": node.x,
                    "y": node.y,
                    "associated_graph": str(node.associated_graph.id),
                    "type": node.type,
                    "color": generate_random_color(),
                    "inputs": node.inputs,
                    "outputs": node.outputs,
                })
                if node.type == "Viewer" and node.input_port != "":
                    affected_nodes[-1]["output_data"] = node.output_data[node.input_port]
                if node.type == "Chart" and node.input_port != "":
                    affected_nodes[-1]["output_data"] = create_svg_chart(node.output_data[node.input_port])

                notif += f"{node}\'s output data has changed.\n"

            self.send(text_data=json.dumps({
                "message": "success",
                "affected_nodes": affected_nodes,
                "notif": notif,
            }))

        elif command == "delete_graph":
            self.send(text_data=json.dumps({
                "message": "success",
                "graph_deleted": "graph_deleted",
            }))

        elif command == "delete_node":
            affected_nodes = []
            for affected_node_id in affected_nodes_from_deletion:
                affected_node = self.graph.get_node(affected_node_id)
                affected_nodes.append({
                    "id": str(affected_node.id),
                    "x": affected_node.x,
                    "y": affected_node.y,
                    "associated_graph": str(affected_node.associated_graph.id),
                    "type": affected_node.type,
                    "color": generate_random_color(),
                    "inputs": affected_node.inputs,
                    "outputs": affected_node.outputs,
                })
            self.send(text_data=json.dumps({
                "message": "success",
                "node_deleted": str(node_id),
                "affected_nodes": affected_nodes,
                "notif": notif,
            }))


class ListGraphsConsumer(WebsocketConsumer):
    def connect(self):
        self.group_name = "list_graphs"

        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name,
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name,
        )

    def handle_command(self, event):
        print("IN HANDLE COMMAND? <List Graphs>")
        command = event.get("command", None)
        name = event.get("name", None)
        id = event.get("id", None)

        if command == "create_graph":
            self.send(text_data=json.dumps({
                "type": "create_graph",
                "name": name,
                "id": id,
            }))
        elif command == "delete_graph":
            self.send(text_data=json.dumps({
                "type": "delete_graph",
                "name": name,
                "id": id,
            }))

