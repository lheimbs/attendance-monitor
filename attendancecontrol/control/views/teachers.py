from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http.response import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, DetailView, DeleteView, UpdateView
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from .. import forms
from ..decorators import teacher_required
from ..models import User, Course, WeekDay, AccessToken
from ..utils import get_users_courses_ongoing_states


class TeacherSignUpView(CreateView):
    model = User
    form_class = forms.TeacherSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'teacher'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('teacher:courses')


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherEdit(UpdateView):
    model = User
    # form_class = TeacherUpdateForm
    fields = ('email', 'first_name', 'last_name')
    template_name = 'control/account_update_form.html'

    # TODO: use UserPassesTestMixin instead of limiting queryset to return forbidden?
    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.id)

    def get_success_url(self):
        return reverse('teacher:courses')


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCoursesList(ListView):
    model = Course
    ordering = ('name', )
    context_object_name = 'courses'
    template_name = 'control/teachers/courses_list.html'

    def get_queryset(self):
        """Sort courses first by ongoing true then false and then ascending by id"""
        courses = self.request.user.teacher.courses.all()
        # not is_ongoing because: True > False
        return sorted(list(courses), key=lambda c: (not c.is_ongoing(), c.id))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['additional_courses'] = self.request.user.teacher.additional_courses.all()
        return ctx


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCourseDetail(DetailView):
    context_object_name = 'course'
    template_name = 'control/teachers/course.html'

    def get_queryset(self):
        return self.request.user.teacher.courses.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['attendance'] = get_course_attendance_data(self.object)
        return ctx


def get_course_dates(course: Course) -> dict:
    next_week = timezone.timedelta(days=7)
    days = {}
    for day in course.sorted_start_times_set:
        start_date = course.start_date
        end_date = course.end_date if course.end_date < timezone.localtime() else timezone.localtime()
        day_times = []
        while start_date < end_date:
            day_times.append(day.get_this_weeks_date(start_date))
            start_date += next_week
        days[day] = day_times
    return days


def get_course_attendance_data(course: Course) -> dict:
    days = get_course_dates(course)
    stud_attendance = []
    for csa in course.coursestudentattendance_set.order_by('student__user__last_name').all():
        stud_days = []
        for day, start_times in days.items():
            stud_attends = []
            for start in start_times:
                end = start + timezone.timedelta(seconds=course.duration*60)
                min_start = start.replace(hour=6, minute=0, second=0, microsecond=0)
                max_start = end - timezone.timedelta(seconds=course.min_attend_time)
                ex_arrival = csa.attendance_dates.filter(arrival__range=[min_start, max_start])
                time_attended = 0
                for ar in ex_arrival:
                    ar_start = start if start > ar.arrival else ar.arrival
                    departure = ar.departure if ar.departure else timezone.localtime()
                    ar_end = end if end < departure else departure
                    time_attended += (ar_end - ar_start).total_seconds()
                status = time_attended / course.min_attend_time * 60
                if status >= 1:
                    status = 'success'
                elif 0.5 >= status > 1:
                    status = 'warning'
                else:
                    status = 'danger'
                stud_attends.append((start, time_attended, status))
            stud_days.append({'name': day.get_day_display(), 'time': day.time.strftime('%H:%M'), 'attendances': stud_attends})
        stud_attendance.append({
            'email': csa.student.user.email,
            'name': csa.student.user.get_full_name(),
            'mat_nr': csa.student.student_nr,
            'days': stud_days
        })
    return stud_attendance


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherAdditionalCourseDetail(DetailView):
    context_object_name = 'course'
    template_name = 'control/teachers/course.html'

    def get_queryset(self):
        return self.request.user.teacher.additional_courses.all()


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCreateCourse(CreateView):
    model = Course
    form_class = forms.CourseCreateForm
    template_name = 'control/teachers/course_add_form.html'

    def get_success_url(self):
        return reverse('teacher:courses')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        ctx = self.get_context_data()
        formset = ctx['week_days_formset']
        if formset.is_valid() and form.is_valid():
            self.object = form.save()
            for teacher in form.cleaned_data['additional_teachers']:
                self.object.additional_teachers.add(teacher)
            for weekday_data in formset.cleaned_data:
                if weekday_data:
                    weekday = WeekDay.objects.create(
                        day=weekday_data['day'], time=weekday_data['time']
                    )
                    self.object.start_times.add(weekday)
            self.request.user.teacher.courses.add(self.object)
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['form'] = forms.CourseCreateForm(self.request.POST, user=self.request.user)
            ctx['week_days_formset'] = forms.WeekDaysFormSet(self.request.POST, prefix="week_days")
        else:
            ctx['form'] = forms.CourseCreateForm(user=self.request.user)
            ctx['week_days_formset'] = forms.WeekDaysFormSet(prefix="week_days")
        return ctx


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherEditCourse(UpdateView):
    model = Course
    form_class = forms.CourseCreateForm
    # fields = ['name', 'min_attend_time', 'duration']
    template_name = 'control/teachers/course_update_form.html'

    def get_success_url(self):
        return reverse('teacher:courses')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        ctx = self.get_context_data()
        formset = ctx['week_days_formset']
        if formset.is_valid() and form.is_valid():
            form.save()
            self.object.additional_teachers.clear()
            for teacher in form.cleaned_data['additional_teachers']:
                self.object.additional_teachers.add(teacher)
            formset.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['form'].initial['additional_teachers'] = self.object.additional_teachers.all()
            ctx['week_days_formset'] = forms.CourseWeekDaysInlineFormSet(
                self.request.POST,
                queryset=self.object.start_times.all(),
                instance=self.object,
                prefix="week_days"
            )
        else:
            ctx['form'].initial['additional_teachers'] = self.object.additional_teachers.all()
            ctx['week_days_formset'] = forms.CourseWeekDaysInlineFormSet(
                prefix="week_days", instance=self.object, queryset=self.object.start_times.all()
            )
        return ctx


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherCourseDelete(DeleteView):
    # TODO: make this into modal (bit more elegant?)
    model = Course
    template_name = 'control/course_confirm_delete.html'

    def get_success_url(self) -> str:
        return reverse_lazy('teacher:courses')

    def get_queryset(self):
        return self.request.user.teacher.courses.all()


@login_required
@teacher_required
def set_access_token(request, pk):
    # Idk how to make these two queries into one - so took the example from django doc and expanded it
    try:
        course = request.user.teacher.courses.get(pk=pk)
    except Course.DoesNotExist:
        try:
            course = request.user.teacher.additional_courses.get(pk=pk)
        except Course.DoesNotExist:
            raise Http404("No Course matches the given query.")

    token = AccessToken.objects.create(valid_time=course.token_valid_time)
    token.save()
    course.access_token = token
    course.save()

    expires = token.created + timezone.timedelta(seconds=token.valid_time*60)
    url = request.build_absolute_uri(course.get_absolute_student_register_url())

    context = {
        'id': course.id,
        'token': token.token,
        'expires': expires,
        'register_url': url
    }
    return render(request, 'control/teachers/course_registration.html', context=context)


@login_required
@teacher_required
def get_courses_states(request):
    courses = get_users_courses_ongoing_states(request.user.teacher)
    return JsonResponse(courses)
