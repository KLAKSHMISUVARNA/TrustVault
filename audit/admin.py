from django.contrib import admin
from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "actor",
        "action",
        "target_type",
        "timestamp",
    )

    readonly_fields = (
        "actor",
        "action",
        "target_type",
        "target_id",
        "metadata",
        "timestamp",
        "previous_hash",
        "event_hash",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False