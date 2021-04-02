from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/probes/student/course/(?P<course_pk>\d+)/$', consumers.StudentCourseProbesConsumer.as_asgi()),
]
