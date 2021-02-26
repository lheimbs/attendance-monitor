from django.urls import path, include

from .views import home, students, teachers

urlpatterns = [
    path('', home.home, name='home'),
    path('students/', include(([
        path('', students.StudentCoursesList.as_view(), name='courses'),
        path('<int:pk>', students.StudentCourseDetail.as_view(), name='course-detail'),
        # path('interests/', students.StudentInterestsView.as_view(), name='student_interests'),
        # path('taken/', students.TakenQuizListView.as_view(), name='taken_quiz_list'),
        # path('quiz/<int:pk>/', students.take_quiz, name='take_quiz'),
    ], 'control'), namespace='students')),
    path('teachers/', include(([
        path('', teachers.TeacherCoursesList.as_view(), name='courses'),
        # path('interests/', students.StudentInterestsView.as_view(), name='student_interests'),
        # path('taken/', students.TakenQuizListView.as_view(), name='taken_quiz_list'),
        # path('quiz/<int:pk>/', students.take_quiz, name='take_quiz'),
    ], 'control'), namespace='teachers')),
]
