from datetime import datetime
from typing import Dict, Union

from django.db.models.query import QuerySet
from django.utils import timezone

from .models import Student, Teacher, ProbeRequest


class DatetimeRange:
    def __init__(self, start_date, end_date):
        if end_date < start_date:
            raise ValueError('end_date {!r} < start_date {!r}'.format(end_date, start_date))

        self.start_date = start_date
        self.end_date = end_date

    def __contains__(self, other):
        """ (start_date, end_date] """
        return self.start_date <= other.start_date < other.end_date < self.end_date

    def __eq__(self, other):
        return (
            (self.start_date == other.start_date)
            and (self.end_date == other.end_date)
        )

    def __and__(self, other):
        """ Return overlapping range for dr1 & dr2. """
        if self.end_date < other.start_date or self.start_date > other.end_date:
            return

        dates = sorted([
            self.start_date,
            self.end_date,
            other.start_date,
            other.end_date
        ])
        return DatetimeRange(dates[1], dates[2])

    def __sub__(self, other):
        """ Return list with ranges """
        intersection = self & other
        if intersection is None:
            return [self]

        result = []
        if intersection.start_date != self.start_date:
            result.append(DatetimeRange(self.start_date, intersection.start_date))
        if intersection.end_date != self.end_date:
            result.append(DatetimeRange(intersection.end_date, self.end_date))
        return result

    def __matmul__(self, other):
        """ Reduce intersecting/overlapping dates into one and return tue new one. 

        Return None if the dates don't overlap/intersect.
        """
        if other.end_date < self.start_date or self.end_date < other.start_date:
            return

        dates = sorted([
            self.start_date,
            self.end_date,
            other.start_date,
            other.end_date
        ])
        return DatetimeRange(dates[0], dates[3])

    @property
    def delta(self):
        return self.end_date - self.start_date

    def __repr__(self):
        return '<DatetimeRange({!r}, {!r}>'.format(
            self.start_date, self.end_date
        )


class DatetimeRangeList:
    def __init__(self, *others):
        self.list = []
        for elem in others:
            self.add(elem)

    def add(self, elem):
        if not self.list:
            self.list = [elem]
            return
        for item in self.list:
            new_item = elem @ item
            if new_item:
                self.list.remove(item)
                return self.add(new_item)
        else:
            self.list.append(elem)

    def __repr__(self):
        return str(self.list)


def get_users_courses_ongoing_states(user_object: Union[Student, Teacher]) -> Dict:
    """Get ongoing state of user courses in a dict of type <id>: <True if ongoing else False>"""
    courses = {}
    if isinstance(user_object, Student):
        for course in user_object.courses.all():
            courses[course.id] = True if course.is_ongoing() else False
    elif isinstance(user_object, Teacher):
        for course in user_object.courses.all():
            courses[course.id] = True if course.is_ongoing() else False
        for course in user_object.additional_courses.all():
            courses[course.id] = True if course.is_ongoing() else False
    return courses


def get_students_probes(student: Student,
                        start_time: datetime = None,
                        end_time: datetime = None) -> QuerySet[ProbeRequest]:
    """Query a students ProbeRequest with optionally supplied time constraints"""
    if student.wifi_info is None:
        return []

    probes_query = ProbeRequest.objects.filter(mac=student.wifi_info.mac)
    if start_time:
        probes_query = probes_query.filter(time__gte=start_time)
    if end_time:
        probes_query = probes_query.filter(time__lt=end_time)
    return probes_query.order_by('time')


def get_students_last_burst_update(student: Student) -> datetime:
    """Get the last time a students burst interval was updated"""
    last_update = student.wifi_info.mac_burst_updated
    if last_update is None:
        last_update = timezone.make_aware(
            ProbeRequest.objects.first().time,
            timezone.get_current_timezone()
        )
    return last_update
