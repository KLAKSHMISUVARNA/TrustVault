from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from .models import Document, DocumentPermission
from audit.models import AuditEvent


User = get_user_model()


class DocumentPermissionViewTests(TestCase):

    def setUp(self):

        self.owner = User.objects.create_user(
            username="document_owner",
            password="TestPassword123!",
            role="OWNER"
        )

        self.viewer = User.objects.create_user(
            username="document_viewer",
            password="TestPassword123!",
            role="VIEWER"
        )

        self.other_user = User.objects.create_user(
            username="other_user",
            password="TestPassword123!",
            role="VIEWER"
        )

        self.document = Document.objects.create(
            owner=self.owner,
            title="Confidential Contract",
            description="Security test document",
            category="CONTRACT",
            file=SimpleUploadedFile(
                "contract.txt",
                b"Test document content",
                content_type="text/plain"
            ),
            original_filename="contract.txt",
            file_size=22
        )

    def test_owner_can_grant_read_permission(self):

        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("grant_permission", args=[self.document.id]),
            {
                "user": self.viewer.id,
                "permission": "READ"
            }
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            DocumentPermission.objects.filter(
                document=self.document,
                user=self.viewer,
                permission="READ",
                is_active=True
            ).exists()
        )

        self.assertTrue(
            AuditEvent.objects.filter(
                action="PERMISSION_GRANTED"
            ).exists()
        )

    def test_owner_can_grant_edit_permission(self):

        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("grant_permission", args=[self.document.id]),
            {
                "user": self.viewer.id,
                "permission": "EDIT"
            }
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            DocumentPermission.objects.filter(
                document=self.document,
                user=self.viewer,
                permission="EDIT",
                is_active=True
            ).exists()
        )

    def test_non_owner_cannot_grant_permission(self):

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("grant_permission", args=[self.document.id]),
            {
                "user": self.viewer.id,
                "permission": "READ"
            }
        )

        self.assertEqual(response.status_code, 404)

        self.assertFalse(
            DocumentPermission.objects.filter(
                document=self.document,
                user=self.viewer
            ).exists()
        )

    def test_owner_can_revoke_permission(self):

        permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            permission="READ"
        )

        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("revoke_permission", args=[permission.id])
        )

        self.assertEqual(response.status_code, 302)

        permission.refresh_from_db()

        self.assertFalse(permission.is_active)
        self.assertIsNotNone(permission.revoked_at)

        self.assertTrue(
            AuditEvent.objects.filter(
                action="PERMISSION_REVOKED"
            ).exists()
        )

    def test_non_owner_cannot_revoke_permission(self):

        permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            permission="READ"
        )

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("revoke_permission", args=[permission.id])
        )

        self.assertEqual(response.status_code, 404)

        permission.refresh_from_db()

        self.assertTrue(permission.is_active)

        self.assertFalse(
            AuditEvent.objects.filter(
                action="PERMISSION_REVOKED"
            ).exists()
        )

    def test_permission_changes_require_post(self):

        self.client.force_login(self.owner)

        permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            permission="READ"
        )

        response = self.client.get(
            reverse("revoke_permission", args=[permission.id])
        )

        self.assertEqual(response.status_code, 405)

        permission.refresh_from_db()
        self.assertTrue(permission.is_active)