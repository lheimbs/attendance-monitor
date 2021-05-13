from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/probes/status/course/$', consumers.StudentCourseStatusConsumer.as_asgi()),
]
