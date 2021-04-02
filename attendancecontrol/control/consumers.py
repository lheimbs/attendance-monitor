import json
from channels.generic.websocket import WebsocketConsumer

from .views import probes

class StudentCourseProbesConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        if self.user.is_student:
            self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        course = self.user.student.courses.get(pk=text_data_json.get('course'))
        fig = probes.get_students_probe_records(self.user.student, course)

        self.send(text_data=json.dumps({
            'graph': fig.to_html(full_html=False)
        }))
