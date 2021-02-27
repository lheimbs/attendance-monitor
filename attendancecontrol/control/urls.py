from django.urls import path, include

from .views import home, students, teachers

urlpatterns = [
    path('', home.home, name='home'),
    path('students/', include(([
        path('', students.StudentCoursesList.as_view(), name='courses'),
        path('course/<int:pk>', students.StudentCourseDetail.as_view(), name='detail'),
        # path('interests/', students.StudentInterestsView.as_view(), name='student_interests'),
        # path('taken/', students.TakenQuizListView.as_view(), name='taken_quiz_list'),
        # path('quiz/<int:pk>/', students.take_quiz, name='take_quiz'),
    ], 'control'), namespace='students')),
    path('teacher/', include(([
        path('', teachers.TeacherCoursesList.as_view(), name='courses'),
        path('course/<int:pk>', teachers.TeacherCourseDetail.as_view(), name='detail'),
        path('new/', teachers.TeacherCreateCourse.as_view(), name='add'),
        path('edit/', teachers.TeacherCoursesList.as_view(), name='edit'),
        path('delete/', teachers.TeacherCoursesList.as_view(), name='delete'),
        # path('quiz/<int:pk>/', students.take_quiz, name='take_quiz'),
    ], 'control'), namespace='teacher')),
]
