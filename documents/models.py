import uuid
import os
from .validators import validate_document_file
from django.db import models
from django.conf import settings


def private_document_path(instance, filename):
    extension = os.path.splitext(filename)[1].lower()

    return f"documents/{uuid.uuid4().hex}{extension}"


class Document(models.Model):

    class Category(models.TextChoices):
        CONTRACT = "CONTRACT", "Contract"
        FINANCE = "FINANCE", "Finance"
        HR = "HR", "Human Resources"
        TECHNICAL = "TECHNICAL", "Technical"
        OTHER = "OTHER", "Other"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_documents"
    )

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER
    )
    file = models.FileField(
    upload_to=private_document_path,
    validators=[validate_document_file]
)

    original_filename = models.CharField(max_length=255)

    file_size = models.PositiveBigIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title