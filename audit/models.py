from django.conf import settings
from django.db import models

from django.utils import timezone
class AuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events"
    )

    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100, blank=True)

    metadata = models.JSONField(default=dict)

    timestamp = models.DateTimeField(default=timezone.now)

    previous_hash = models.CharField(max_length=64)
    event_hash = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.action} - {self.timestamp}"