from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from .models import AuditEvent
from .services import verify_audit_chain


@login_required
def admin_audit_dashboard(request):
    if getattr(request.user, "role", None) != "ADMIN":
        raise PermissionDenied("Only administrators can view the audit trail.")

    # Fixed: use 'timestamp' instead of 'created_at'
    events = AuditEvent.objects.all().order_by("-timestamp")
    is_valid = verify_audit_chain()

    return render(
        request,
        "audit/admin_dashboard.html",
        {
            "events": events,
            "chain_valid": is_valid,
        },
    )