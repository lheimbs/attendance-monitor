import json
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async

from .views import probes


class StudentCourseProbesConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        if self.user.is_student:
            self.accept()
        else:
            self.close()

    def disconnect(self, close_code):
        pass

    @database_sync_to_async
    def get_course(self, course_pk):
        return self.user.student.courses.get(pk=course_pk)
    
    @database_sync_to_async
    def get_students_probes_fig(self, course):
        return probes.get_students_probe_records(self.user.student, course)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        course = await self.get_course(text_data_json.get('course'))
        fig = await self.get_students_probes_fig(course)

        self.send(text_data=json.dumps({
            'graph': fig.to_html(full_html=False)
        }))
