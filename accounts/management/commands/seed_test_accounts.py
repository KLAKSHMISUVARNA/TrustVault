import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Seed test accounts with dedicated roles for hackathon evaluation."

    def handle(self, *args, **options):
        accounts = [
            ("admin_test", "admin@trustvault.local", "AdminPass2026!", User.Role.ADMIN),
            ("owner_test", "owner@trustvault.local", "OwnerPass2026!", User.Role.OWNER),
            ("editor_test", "editor@trustvault.local", "EditorPass2026!", User.Role.VIEWER),
            ("viewer_test", "viewer@trustvault.local", "ViewerPass2026!", User.Role.VIEWER),
        ]

        for username, email, default_password, role in accounts:
            password = os.getenv(f"SEED_{role}_PASSWORD", default_password)
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email, "role": role},
            )
            user.set_password(password)
            user.role = role
            user.is_active = True
            if role == User.Role.ADMIN:
                user.is_staff = True
            user.save()

            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{status} {role} account: {username}"))