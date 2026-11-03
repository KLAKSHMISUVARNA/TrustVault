import os

from django.core.exceptions import ValidationError


MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
}


def validate_document_file(uploaded_file):

    extension = os.path.splitext(uploaded_file.name)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError("File type not allowed.")

    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValidationError("Maximum file size is 10 MB.")

    if uploaded_file.size == 0:
        raise ValidationError("Empty files are not allowed.")