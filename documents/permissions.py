from audit.services import record_audit_event
from django.core.exceptions import PermissionDenied


def get_client_ip(request):
  x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
  if x_forwarded_for:
    return x_forwarded_for.split(",")[0].strip()
  return request.META.get("REMOTE_ADDR")


def can_access_document(user, document, required_permission="READ"):
  if not user.is_authenticated or not user.is_active:
    return False

  if getattr(user, "role", None) == "ADMIN":
    return True

  if document.owner_id == user.id:
    return True

  perm_query = document.permissions.filter(
      user=user,
      is_active=True,
  )

  if required_permission == "EDIT":
    return perm_query.filter(permission="EDIT").exists()
  else:
    return perm_query.filter(permission__in=["READ", "EDIT"]).exists()


def check_document_access(request, document, required_level="READ"):
  user = request.user

  if not can_access_document(
      user, document, required_permission=required_level
  ):
    record_audit_event(
        actor=user if user.is_authenticated else None,
        document=document,
        action="DOCUMENT_ACCESS_DENIED",
        details=f"Denied {required_level} attempt on document {document.id}",
        ip_address=get_client_ip(request),
    )
    raise PermissionDenied("You do not have permission to perform this action.")

  return True