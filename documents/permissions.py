from .models import DocumentPermission


def can_access_document(user, document, permission="READ"):

    if not user.is_authenticated or not user.is_active:
        return False

    # Document owner has full access
    if document.owner_id == user.id:
        return True

    # Administrators do not automatically access documents
    if user.role == "ADMIN":
        return False

    allowed_permissions = ["READ"]

    if permission == "EDIT":
        allowed_permissions = ["EDIT"]

    elif permission == "READ":
        allowed_permissions = ["READ", "EDIT"]

    else:
        return False

    return DocumentPermission.objects.filter(
        document=document,
        user=user,
        permission__in=allowed_permissions,
        is_active=True
    ).exists()