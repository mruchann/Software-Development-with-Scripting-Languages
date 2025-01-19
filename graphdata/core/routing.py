from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/<uuid:graph_id>/', consumers.GraphConsumer.as_asgi()),
    path('ws/listgraphs/', consumers.ListGraphsConsumer.as_asgi()),
]
