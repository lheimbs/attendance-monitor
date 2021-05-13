from channels.generic.websocket import JsonWebsocketConsumer


class StudentCourseStatusConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        if self.user.is_student or self.user.is_teacher:
            self.accept()
            if self.user.is_student:
                self.user = self.user.student
            elif self.user.is_teacher:
                self.user = self.user.teacher
        else:
            self.close()

    def disconnect(self, close_code):
        pass

    def receive_json(self, content, **kwargs):
        super().receive_json(content, **kwargs)
        courses = {}
        for course in self.user.courses.all():
            courses[course.id] = True if course.is_ongoing() else False
        self.send_json(courses)
