from django.contrib import admin
from .models import Document


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