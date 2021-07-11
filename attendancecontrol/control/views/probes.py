import logging
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
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .. import models
from .. import utils
from ..decorators import student_required
from ..serializers import ProbeRequestSerializer

logger = logging.getLogger('control')

@api_view(['POST'])
def incoming_probe_view(request):
    if request.method == 'POST':
        serializer = ProbeRequestSerializer(data=request.data.dict())
        if serializer.is_valid():
            check_for_departure()

            probe = serializer.save()
            if models.WifiInfo.objects.filter(mac=probe.mac).exists():
                # Only consume probes for registered macs
                w_info = models.WifiInfo.objects.get(mac=probe.mac)
                probe.mac_addr = w_info
                probe.save()

                update_burst_interval_variance(probe)

                logger.debug(f'ADD {probe.mac}: {probe.time}')
                consume_probe(probe)
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_403_FORBIDDEN)


def check_for_departure():
    """Get all macs that are in ARRIVAL state and have a student and check for potential departure."""
    for mac in models.WifiInfo.objects.filter(state=models.State.POTENTIAL_DEPARTURE).exclude(student=None):
        try:
            mac.departure_threshold()
            mac.save()
            logger.debug(f"{mac!r}: State.POTENTIAL_DEPARTURE -> State.DEPARTURE")
        except models.DepartureThreshholdNotReachedError:
            pass
    for mac in models.WifiInfo.objects.filter(state=models.State.ARRIVAL).exclude(student=None):
        try:
            mac.without_probes_recently()
            mac.save()
            logger.debug(f"{mac!r}: State.ARRIVAL -> State.POTENTIAL_DEPARTURE")
        except models.WithdrawalThresholdNotReachedError:
            pass


def consume_probe(probe: models.ProbeRequest) -> None:  # noqa C901
    logger.debug(f"{probe!r}: intial state: {probe.mac_addr.state}")

    if probe.mac_addr.state == models.State.INITIAL:
        probe.mac_addr.initial_probe_detected(probe)
        logger.debug(f"{probe!r}: State.INITIAL -> State.POTENTIAL_ARRIVAL")

    elif probe.mac_addr.state == models.State.POTENTIAL_ARRIVAL:
        try:
            probe.mac_addr.arrival_threshold(probe)
            logger.debug(f"{probe!r}: State.POTENTIAL_ARRIVAL -> State.ARRIVAL")
            # add_arrival(probe.mac_addr, probe.time)
        except models.ArrivalThreshholdExceededError:
            probe.mac_addr.arrival_threshold_exceeded()
            logger.debug(
                f"{probe!r}: ArrivalThreshholdExceededError: "
                "State.POTENTIAL_ARRIVAL -> State.INITIAL"
            )

    elif probe.mac_addr.state == models.State.ARRIVAL:
        try:
            probe.mac_addr.without_probes_recently(probe)
            logger.debug(f"{probe!r}: State.ARRIVAL -> State.POTENTIAL_DEPARTURE")
        except models.WithdrawalThresholdNotReachedError:
            logger.debug(f"{probe!r}: WithdrawalThresholdNotReachedError")

    elif probe.mac_addr.state == models.State.POTENTIAL_DEPARTURE:
        try:
            probe.mac_addr.departure_threshold(probe)
            logger.debug(f"{probe!r}: State.POTENTIAL_DEPARTURE -> State.DEPARTURE")
        except models.DepartureThreshholdNotReachedError:
            probe.mac_addr.probe_detected(probe)
            logger.debug(
                f"{probe!r}: DepartureThreshholdNotReachedError: "
                "State.POTENTIAL_DEPARTURE -> State.ARRIVAL"
            )

    if probe.mac_addr.state == models.State.DEPARTURE:
        # add_departure(probe.mac_addr, probe.time)
        probe.mac_addr.initial()
        logger.debug(f"{probe!r}: State.DEPARTURE -> State.INITIAL")

    probe.mac_addr.save()
    probe.save()
    logger.debug("after: {}".format(probe.mac_addr.state))


def update_burst_interval_variance(probe: models.ProbeRequest):
    # Have we recorded any probes before?
    if probe.mac_addr.burst_count == 0:
        logger.debug(f"First recieved probe or mac {probe.mac_addr!r}")
        probe.mac_addr.burst_count = 1
        probe.mac_addr.burst_update = probe.time
        probe.mac_addr.save()
        return

    last_probe = models.ProbeRequest.objects.filter(mac=probe.mac).last()
    if not last_probe:
        logger.error(f"No previous probe recorded for mac {probe.mac_addr!r}")
        return

    if timezone.is_naive(last_probe.time):
        last_probe.time = timezone.get_current_timezone().localize(last_probe.time)
        last_probe.save()

    logger.debug(f"probe {probe.time}, last: {last_probe.time}")
    time_diff = (probe.time - last_probe.time).total_seconds()
    if time_diff < 1:
        logger.debug(f"Probe is part of burst. Skipping interval calculation. {probe!r}")
        return

    logger.debug(
        f"Previous: interval={probe.mac_addr.burst_interval}, variance={probe.mac_addr.burst_variance}, "
        f"count={probe.mac_addr.burst_count}"
    )
    prev_interval = probe.mac_addr.burst_interval
    probe.mac_addr.burst_count += 1
    probe.mac_addr.burst_interval = prev_interval \
        + (time_diff - prev_interval) / probe.mac_addr.burst_count
    probe.mac_addr.burst_variance = probe.mac_addr.burst_variance \
        + (time_diff - probe.mac_addr.burst_interval) * (time_diff - prev_interval)
    probe.mac_addr.burst_update = probe.time
    probe.mac_addr.save()
    logger.debug(
        f"After: interval={probe.mac_addr.burst_interval}, variance={probe.mac_addr.burst_variance}, "
        f"count={probe.mac_addr.burst_count}"
    )


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
        if student.wifi_info.burst_count == 0:
            interval = statistics.mean(deltas)
            probes_count = len(deltas)
            ret_val = 1
        else:
            # See incremental averaging: https://math.stackexchange.com/a/106720
            old_interval = interval
            count = student.wifi_info.burst_count
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
    """ Set/Update a students burst_interval average.

    Update a students burst interval at max once daily,
    by getting all date ranges in which the students courses are ongoing,
    calculating the time deltas between recieved probes and generating a
    running average of deltas that are greater than one second.
    The one second cut-off is used to distinguish between probes sent in a burst
    (which are not of interest) and the time between such bursts.
    """
    latest_update = student.wifi_info.burst_updated  # - timezone.timedelta(days=7)
    if latest_update is None:
        latest_update = timezone.get_current_timezone().localize(
            models.ProbeRequest.objects.first().time,
        )
    if latest_update and latest_update > timezone.now().replace(hour=0, minute=0, second=0, microsecond=0):
        # update at most once daily
        return

    query_date = timezone.now()
    interval = student.wifi_info.burst_interval
    count = student.wifi_info.burst_count
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

            student.wifi_info.burst_interval = interval
            student.wifi_info.burst_count = count
            student.wifi_info.burst_updated = query_date
            student.wifi_info.save()


def get_start_date(datetime: datetime, dates: utils.DatetimeRangeList) -> datetime:
    for date in dates.list:
        if date.start_date <= datetime < date.end_date:
            return date.start_date
    return None


def get_students_probe_records(student: models.Student,
                               course: models.Course) -> str:
    query_date = timezone.localtime()
    course_date = course.start_date
    dates = utils.DatetimeRangeList()
    while course_date < query_date:
        for weekday in course.start_times.all():
            start_date = weekday.get_this_weeks_date(course_date)
            end_date = get_course_end_date(start_date, course.duration)
            if start_date < end_date:
                dates.add(utils.DatetimeRange(start_date, end_date))
        course_date += timezone.timedelta(days=7)

    query = reduce(operator.or_, (Q(time__range=[date.start_date, date.end_date]) for date in dates.list))
    probe_times = models.ProbeRequest.objects.filter(query, mac=student.wifi_info.mac)\
        .order_by('time').values_list('time', flat=True)

    course_dates = []
    minutes = []
    for probe_time in probe_times:
        probe_time = timezone.make_aware(probe_time, timezone.utc)
        start_date = get_start_date(probe_time, dates)
        course_dates.append(start_date.strftime('%a, %d.%m %H:%M'))
        minutes.append((probe_time - start_date).total_seconds() // 60)

    # print(course_dates)
    height = len(set(course_dates)) * 25

    return px.strip(
        x=minutes, y=course_dates,
        labels={'x': 'Minute', 'y': 'Date'},
        range_x=[-0.2, course.duration],
        title=f"Recorded Probes for course {course.name}",
        height=height
    )
