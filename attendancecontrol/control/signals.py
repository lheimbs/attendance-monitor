from django.contrib.auth.signals import user_logged_in
# from django.db.models.signals import m2m_changed
# from django.dispatch import receiver

# from .models import Course
from .views.probes import update_student_burst_info

# @receiver(m2m_changed, sender=Course.start_times.through)
# def check_orphan_items(sender, instance, action, reverse, model, **kwargs):
#     for item in model.objects.all():
#         if not item.course_set.all().exists():
#             item.delete()


def update_students_burst(sender, user, request, **kwargs):
    if user.is_student:
        print("Student logged in", user.student)
        update_student_burst_info(user.student)


# user_logged_in.connect(update_students_burst)
