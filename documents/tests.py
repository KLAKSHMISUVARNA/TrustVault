from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from tempfile import TemporaryDirectory

from .models import Document, DocumentPermission
from .permissions import can_access_document


User = get_user_model()


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class DocumentPermissionTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            password="TestPassword123!",
            role="OWNER"
        )

        self.viewer = User.objects.create_user(
            username="viewer",
            password="TestPassword123!",
            role="VIEWER"
        )

        self.unauthorized = User.objects.create_user(
            username="unauthorized",
            password="TestPassword123!",
            role="VIEWER"
        )

        self.document = Document.objects.create(
            owner=self.owner,
            title="Confidential Contract",
            description="Test document",
            category="CONTRACT",
            file=SimpleUploadedFile(
                "contract.txt",
                b"Test document content",
                content_type="text/plain"
            ),
            original_filename="contract.txt",
            file_size=22
        )

    def test_owner_can_access_document(self):
        self.assertTrue(
            can_access_document(self.owner, self.document, "READ")
        )

        self.assertTrue(
            can_access_document(self.owner, self.document, "EDIT")
        )

    def test_unauthorized_user_cannot_access_document(self):
        self.assertFalse(
            can_access_document(self.unauthorized, self.document, "READ")
        )

    def test_read_permission_allows_read_only(self):
        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            permission="READ"
        )

        self.assertTrue(
            can_access_document(self.viewer, self.document, "READ")
        )

        self.assertFalse(
            can_access_document(self.viewer, self.document, "EDIT")
        )

    def test_edit_permission_allows_read_and_edit(self):
        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            permission="EDIT"
        )

        self.assertTrue(
            can_access_document(self.viewer, self.document, "READ")
        )

        self.assertTrue(
            can_access_document(self.viewer, self.document, "EDIT")
        )

    def test_revoked_permission_denies_access(self):
        permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            permission="READ"
        )

        permission.is_active = False
        permission.save()

        self.assertFalse(
            can_access_document(self.viewer, self.document, "READ")
        )

    def test_inactive_user_cannot_access_document(self):
        self.viewer.is_active = False
        self.viewer.save()

        self.assertFalse(
            can_access_document(self.viewer, self.document, "READ")
        )

    def test_invalid_permission_type_is_denied(self):
        self.assertFalse(
            can_access_document(self.viewer, self.document, "DELETE")
        )