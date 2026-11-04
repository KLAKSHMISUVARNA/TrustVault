import tempfile

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from .models import Document, DocumentPermission
from audit.models import AuditEvent


User = get_user_model()


class UploadDownloadSecurityTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.temp_storage = tempfile.TemporaryDirectory()
        cls.settings_override = override_settings(
            MEDIA_ROOT=cls.temp_storage.name
        )
        cls.settings_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        cls.temp_storage.cleanup()
        super().tearDownClass()

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_test",
            password="TestPassword123!",
            role="OWNER"
        )

        self.viewer = User.objects.create_user(
            username="viewer_test",
            password="TestPassword123!",
            role="VIEWER"
        )

        self.other_user = User.objects.create_user(
            username="other_test",
            password="TestPassword123!",
            role="VIEWER"
        )

    def create_document(self):
        return Document.objects.create(
            owner=self.owner,
            title="Security Test Document",
            description="Testing secure downloads",
            category="CONTRACT",
            file=SimpleUploadedFile(
                "security.txt",
                b"Confidential test content",
                content_type="text/plain"
            ),
            original_filename="security.txt",
            file_size=25
        )

    def test_owner_can_upload_document(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("upload_document"),
            {
                "title": "New Contract",
                "description": "Upload test",
                "category": "CONTRACT",
                "file": SimpleUploadedFile(
                    "contract.txt",
                    b"Contract content",
                    content_type="text/plain"
                )
            }
        )

        self.assertEqual(response.status_code, 302)

        document = Document.objects.get(title="New Contract")

        self.assertEqual(document.owner, self.owner)
        self.assertTrue(document.file.storage.exists(document.file.name))

        self.assertTrue(
            AuditEvent.objects.filter(
                action="DOCUMENT_UPLOADED"
            ).exists()
        )

    def test_viewer_cannot_upload_document(self):
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("upload_document"),
            {
                "title": "Unauthorized Upload",
                "description": "Test",
                "category": "CONTRACT",
                "file": SimpleUploadedFile(
                    "test.txt",
                    b"Test content",
                    content_type="text/plain"
                )
            }
        )

        self.assertEqual(response.status_code, 403)

        self.assertFalse(
            Document.objects.filter(
                title="Unauthorized Upload"
            ).exists()
        )

    def test_owner_can_download_document(self):
        document = self.create_document()
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("download_document", args=[document.id])
        )

        try:
            self.assertEqual(response.status_code, 200)

            content = b"".join(response.streaming_content)

            self.assertEqual(content, b"Confidential test content")

            self.assertTrue(
                AuditEvent.objects.filter(
                    action="DOCUMENT_DOWNLOADED"
                ).exists()
            )
        finally:
            response.close()

    def test_read_permission_allows_download(self):
        document = self.create_document()

        DocumentPermission.objects.create(
            document=document,
            user=self.viewer,
            permission="READ"
        )

        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse("download_document", args=[document.id])
        )

        try:
            self.assertEqual(response.status_code, 200)
        finally:
            response.close()

    def test_edit_permission_allows_download(self):
        document = self.create_document()

        DocumentPermission.objects.create(
            document=document,
            user=self.viewer,
            permission="EDIT"
        )

        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse("download_document", args=[document.id])
        )

        try:
            self.assertEqual(response.status_code, 200)
        finally:
            response.close()

    def test_unauthorized_user_cannot_download(self):
        document = self.create_document()
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse("download_document", args=[document.id])
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            AuditEvent.objects.filter(
                action="DOCUMENT_ACCESS_DENIED"
            ).exists()
        )

    def test_revoked_user_cannot_download(self):
        document = self.create_document()

        permission = DocumentPermission.objects.create(
            document=document,
            user=self.viewer,
            permission="READ"
        )

        self.client.force_login(self.viewer)

        # Confirm access before revocation.
        first_response = self.client.get(
            reverse("download_document", args=[document.id])
        )

        try:
            self.assertEqual(first_response.status_code, 200)
        finally:
            first_response.close()

        # Revoke permission.
        permission.is_active = False
        permission.save()

        # Attempt access again.
        second_response = self.client.get(
            reverse("download_document", args=[document.id])
        )

        self.assertEqual(second_response.status_code, 403)