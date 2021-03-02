from django.urls import path, include

from .views import home, students, teachers

urlpatterns = [
    path('', home.home, name='home'),
    path('student/', include(([
        path('', students.StudentCoursesList.as_view(), name='courses'),
        path('course/<int:pk>', students.StudentCourseDetail.as_view(), name='detail'),
        path('course/register/<int:pk>/<str:token>', students.register_student_for_course, name='register_course'),
        path('course/register', students.manual_register_student_for_course, name='register_course_manual'),
        path('course/leave/<int:pk>', students.student_leave_course, name='leave_course'),
        path('account/edit/<int:pk>/', students.StudentEdit.as_view(), name='edit_account'),
    ], 'control'), namespace='student')),
    path('teacher/', include(([
        path('', teachers.TeacherCoursesList.as_view(), name='courses'),
        path('course/<int:pk>', teachers.TeacherCourseDetail.as_view(), name='detail'),
        path('new/', teachers.TeacherCreateCourse.as_view(), name='add'),
        path('edit/<int:pk>', teachers.TeacherEditCourse.as_view(), name='edit'),
        path('delete/<int:pk>', teachers.TeacherCourseDelete.as_view(), name='delete'),
        path('course/enable/<int:pk>/', teachers.set_access_token, name='enable_course'),
        path('account/edit/<int:pk>/', teachers.TeacherEdit.as_view(), name='edit_account'),
    ], 'control'), namespace='teacher')),
]
