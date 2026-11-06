import os
import zipfile
from django.core.exceptions import ValidationError

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
}

# Magic byte signatures
SIGNATURE_PDF = b"%PDF"
SIGNATURE_PNG = b"\x89PNG\r\n\x1a\n"
SIGNATURE_JPEG = b"\xff\xd8\xff"
SIGNATURE_ZIP = b"PK\x03\x04"  # Base signature for DOCX


def validate_document_file(uploaded_file):
    # 1. Check file size boundaries
    if uploaded_file.size == 0:
        raise ValidationError("Empty files are not allowed.")

    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValidationError("Maximum file size is 10 MB.")

    # 2. Check extension
    extension = os.path.splitext(uploaded_file.name)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError("File type not allowed.")

    # 3. Read header bytes for signature verification
    # Read up to 2048 bytes to inspect magic numbers and text encoding
    header = uploaded_file.read(2048)
    # Reset stream pointer so subsequent saving/processing has full file content
    uploaded_file.seek(0)

    # 4. Strict Magic Byte Verification by Extension
    if extension == ".pdf":
        if not header.startswith(SIGNATURE_PDF):
            raise ValidationError("Invalid PDF format: file signature mismatch.")

    elif extension == ".png":
        if not header.startswith(SIGNATURE_PNG):
            raise ValidationError("Invalid PNG format: file signature mismatch.")

    elif extension in [".jpg", ".jpeg"]:
        if not header.startswith(SIGNATURE_JPEG):
            raise ValidationError("Invalid JPEG format: file signature mismatch.")

    elif extension == ".docx":
        # A valid .docx file is an OpenXML ZIP archive containing '[Content_Types].xml'
        if not header.startswith(SIGNATURE_ZIP):
            raise ValidationError("Invalid DOCX format: file signature mismatch.")
        try:
            with zipfile.ZipFile(uploaded_file) as zf:
                namelist = zf.namelist()
                if "[Content_Types].xml" not in namelist:
                    raise ValidationError("Corrupt or invalid DOCX document package.")
        except zipfile.BadZipFile:
            raise ValidationError("Invalid DOCX format: corrupted archive.")
        finally:
            uploaded_file.seek(0)

    elif extension == ".txt":
        # Disallow dangerous executable header bytes masquerading as txt (e.g. PE 'MZ', ELF '\x7fELF')
        if header.startswith(b"MZ") or header.startswith(b"\x7fELF"):
            raise ValidationError("Binary executable content detected in text file.")
        try:
            # Verify text is decodable as utf-8 or ascii
            header.decode("utf-8")
        except UnicodeDecodeError:
            raise ValidationError("Invalid text file: content contains non-text binary data.")