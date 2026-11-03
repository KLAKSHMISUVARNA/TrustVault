from django.contrib import admin
from .models import Document, DocumentPermission


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "owner",
        "category",
        "created_at",
    )

    search_fields = (
        "title",
        "owner__username",
    )

    list_filter = (
        "category",
        "created_at",
    )

    readonly_fields = (
        "owner",
        "original_filename",
        "file_size",
        "created_at",
        "updated_at",
    )


@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):

    list_display = (
        "document",
        "user",
        "permission",
        "is_active",
        "granted_at",
    )

    readonly_fields = (
        "document",
        "user",
        "permission",
        "granted_at",
        "revoked_at",
    )