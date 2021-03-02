# from django.db.models.signals import m2m_changed
# from django.dispatch import receiver

# from .models import Course

# @receiver(m2m_changed, sender=Course.start_times.through)
# def check_orphan_items(sender, instance, action, reverse, model, **kwargs):
#     for item in model.objects.all():
#         if not item.course_set.all().exists():
#             item.delete()
