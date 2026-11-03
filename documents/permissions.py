from .models import Document


def can_access_document(user, document, permission="READ"):

    if not user.is_authenticated:
        return False

    if not user.is_active:
        return False

    if document.owner_id == user.id:
        return True

    return DocumentPermission.objects.filter(
        document=document,
        user=user,
        permission=permission,
        is_active=True
    ).exists()


from django.db import models

  class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "user", "permission"],
                name="unique_document_user_permission"
            )
        ]