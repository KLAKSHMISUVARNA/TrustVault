from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RegistrationSecurityTests(TestCase):
    def test_public_registration_defaults_to_viewer(self):
        """Verify that public registration always assigns VIEWER role."""
        payload = {
            "username": "attacker",
            "email": "attacker@example.com",
            "password1": "SecurePass2026!#",
            "password2": "SecurePass2026!#",
        }
        # Try both 'register' and 'accounts:register'
        try:
            url = reverse("register")
        except Exception:
            url = reverse("accounts:register")

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(username="attacker")
        self.assertEqual(user.role, User.Role.VIEWER)

    def test_public_registration_cannot_inject_admin_role(self):
        """Verify that tampering with POST payload to request ADMIN role is ignored."""
        payload = {
            "username": "fake_admin",
            "email": "fake_admin@example.com",
            "password1": "SecurePass2026!#",
            "password2": "SecurePass2026!#",
            "role": User.Role.ADMIN,
            "setup_key": "TrustVaultAdmin2026",
        }
        try:
            url = reverse("register")
        except Exception:
            url = reverse("accounts:register")

        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(username="fake_admin")
        self.assertEqual(user.role, User.Role.VIEWER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)