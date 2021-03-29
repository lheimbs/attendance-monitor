import operator
import statistics
from functools import reduce
from datetime import datetime
from typing import List, Tuple

import plotly_express as px
from django.db.models import Q
from django.http.response import JsonResponse
from django.utils import timezone
from django.db.models.query import QuerySet

from .. import models
from .. import utils
from ..decorators import student_required


@student_required
def get_students_attendance_currently_ongoing(request):
    student = request.user.student

    # starting primitive: only search for users exact mac
    attendance = {}
    for course in student.courses.all():
        course_ongoing = course.is_ongoing()
        if course_ongoing:
            if course.name not in attendance.keys():
                attendance[course.name] = {}
            weekday, start_time, end_time = course_ongoing
            probes = utils.get_students_probes(student, start_time, end_time)
            attendance[course.name].update({
                'num_probes': len(probes),
                'probes': [probe.time.isoformat() for probe in probes]
            })
            print(course.name, student.wifi_info.mac if student.wifi_info else '', probes)
    return JsonResponse(attendance)


@student_required
def get_student_course_probes_graph(request, course_pk):
    student = request.user.student
    course = student.courses.get(pk=course_pk)
    fig = get_students_probe_records(student, course)
    # TODO: include plotly.js in static files to be gdpr compliant
    return JsonResponse({'graph': fig.to_html(full_html=False)})


def get_probes_burst_deltas(probes_query: QuerySet[models.ProbeRequest]) -> List[float]:
    """Get timedeltas between recieved probe-requests in seconds"""
    deltas = []
    for i, probe in enumerate(probes_query):
        if i == 0:
            continue
        delta = probe.time - probes_query[i-1].time
        # Filter timedeltas that are less than one second out.
        # These are not needed, because they are most likely sent during a burst.
        # We are interested in the average time between bursts
        if delta.total_seconds() > 1:
            deltas.append(delta.total_seconds())
    return deltas


def update_burst_interval(student: models.Student,
                          probes_query: QuerySet[models.ProbeRequest],
                          interval: float,
                          probes_count: int) -> Tuple[int, float, int]:
    """Get timedeltas between recieved probe-requests and calculate the average delta in seconds.

    return codes:
        0: if no deltas supplied.
        1: if initial average is calculated.
        2: if incremental averaging is used.
    returns:
        return code, average_delta, count of processed probes
    """
    deltas = get_probes_burst_deltas(probes_query)
    if not deltas:
        ret_val = 0
    else:
        # Calculate the mean probe burst interval
        if student.wifi_info.mac_burst_count == 0:
            interval = statistics.mean(deltas)
            probes_count = len(deltas)
            ret_val = 1
        else:
            # See incremental averaging: https://math.stackexchange.com/a/106720
            old_interval = interval
            count = student.wifi_info.mac_burst_count
            for delta in deltas:
                count += 1
                new_interval = old_interval + (delta-old_interval) / count
                old_interval = new_interval
            interval = old_interval
            probes_count = count
            ret_val = 2
    return ret_val, interval, probes_count


def get_course_end_date(start_date: datetime, duration: int, query_date: datetime = None) -> datetime:
    end_date = start_date + timezone.timedelta(minutes=duration)
    if query_date and end_date > query_date:
        end_date = query_date
    if end_date < start_date:
        return start_date
    return end_date


def get_missing_dates(last_update: datetime, query_date: datetime, student: models.Student) -> QuerySet:
    dates = utils.DatetimeRangeList()
    while last_update < query_date:
        for course in student.courses.all():
            for weekday in course.start_times.all():
                start_date = weekday.get_this_weeks_date(last_update)
                end_date = get_course_end_date(
                    start_date, course.duration, query_date
                )
                if start_date < end_date:
                    dates.add(utils.DatetimeRange(start_date, end_date))
        last_update += timezone.timedelta(days=7)
    # return sorted(dates, key=lambda d: d[0])
    return dates


def update_student_burst_info(student: models.Student) -> None:
    """ Set/Update a students mac_burst_interval average.

    Update a students burst interval at max once daily,
    by getting all date ranges in which the students courses are ongoing,
    calculating the time deltas between recieved probes and generating a
    running average of deltas that are greater than one second.
    The one second cut-off is used to distinguish between probes sent in a burst
    (which are not of interest) and the time between such bursts.
    """
    latest_update = student.wifi_info.mac_burst_updated  # - timezone.timedelta(days=7)
    if latest_update is None:
        latest_update = timezone.make_aware(
            models.ProbeRequest.objects.first().time,
            timezone.get_current_timezone()
        )
    if latest_update and latest_update > timezone.now().replace(hour=0, minute=0, second=0, microsecond=0):
        # update at most once daily
        return

    query_date = timezone.now()
    interval = student.wifi_info.mac_burst_interval
    count = student.wifi_info.mac_burst_count
    dates = get_missing_dates(latest_update, query_date, student)
    for date in dates.list:
        missed_probes = models.ProbeRequest.objects.filter(
            mac=student.wifi_info.mac,
            time__range=(date.start_date, date.end_date)
        ).order_by('time')
        ret_val, interval, count = update_burst_interval(
            student, missed_probes, interval, count
        )
        if ret_val:
            print(
                "probes:", missed_probes.count(),
                "mean:", interval,
                "count:", count
            )

            student.wifi_info.mac_burst_interval = interval
            student.wifi_info.mac_burst_count = count
            student.wifi_info.mac_burst_updated = query_date
            student.wifi_info.save()


def get_students_probe_records(student: models.Student,
                               course: models.Course) -> str:
    query_date = timezone.now()
    course_date = course.start_date
    dates = utils.DatetimeRangeList()
    while course_date < query_date:
        for weekday in course.start_times.all():
            start_date = weekday.get_this_weeks_date(course_date)
            end_date = get_course_end_date(start_date, course.duration)
            if start_date < end_date:
                dates.add(utils.DatetimeRange(start_date, end_date))
        course_date += timezone.timedelta(days=7)

    course_dates = []
    minutes = []
    probescount = 0
    for date in dates.list:
        start_str = date.start_date.strftime('%a, %d.%m %H:%M')
        probs = models.ProbeRequest.objects.filter(
            mac=student.wifi_info.mac,
            time__range=[date.start_date, date.end_date]
        )
        probescount += probs.count()
        # if probs.count() == 0:
        #     course_dates.append(start_str)
        #     minutes.append(0)
        for probe in probs:
            probe_time = timezone.make_aware(probe.time, timezone.utc)
            course_dates.append(start_str)
            minutes.append((probe_time - date.start_date).total_seconds() // 60)

    return px.strip(
        x=minutes, y=course_dates,
        labels={'x': 'Minutes', 'y': 'Dates'},
        range_x=[-0.1, course.duration],
        title=f"Recorded Probes for course {course.name}"
    )
