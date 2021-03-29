from django.utils import timezone
from django.db import models

class BaseUpdatingModel(models.Model):
    class Meta:
        abstract = True

    created = models.DateTimeField(editable=False, blank=True, null=True)
    modified = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.pk:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super().save(*args, **kwargs)
