import logging
from math import floor

from channels.generic.websocket import JsonWebsocketConsumer

from . import models

logger = logging.getLogger('control')

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
        logger.debug(f"Course status recieved: {content}")
        courses = {}
        for course in self.user.courses.all():
            courses[course.id] = True if course.is_ongoing() else False
        self.send_json(courses)


class StudentCourseAttendanceConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        # self.accept()
        if self.user.is_student:
            self.accept()
        else:
            logger.debug(f"Denied websocket for user {self.user}")
            self.close()

    def disconnect(self, close_code):
        logger.debug(f"Disconnecting websocket with code: {close_code}")

    def receive_json(self, content, **kwargs):
        super().receive_json(content, **kwargs)
        course = models.Course.objects.get(pk=content["course"])
        attendance = {}

        if course.is_ongoing():
            csa = models.CourseStudentAttendance.objects.get(
                course=course,
                student=self.user.student
            )
            current_present = csa.get_current_attendance(minutes=True)
            attendance['current_present'] = round(current_present, 1)
            current_present_percent = (current_present / course.duration) * 100
            attendance['current_present_percent'] = floor(current_present_percent)
            attendance['current_present_percent_5'] = int(floor(current_present_percent / 5.0) * 5.0)

        logger.debug(f"Send to attendance consumer: {attendance}")
        self.send_json(attendance)
