from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone

from .models import Document, DocumentPermission
from .forms import GrantPermissionForm
from audit.services import record_event


@login_required
def grant_permission(request, document_id):

    document = get_object_or_404(
        Document,
        id=document_id,
        owner=request.user
    )

    if request.method == "POST":

        form = GrantPermissionForm(request.POST)

        if form.is_valid():

            recipient = form.cleaned_data["user"]
            permission_type = form.cleaned_data["permission"]

            # Additional server-side security checks
            if (
                recipient.id == request.user.id
                or not recipient.is_active
                or recipient.role == "ADMIN"
            ):
                record_event(
                    actor=request.user,
                    action="PERMISSION_GRANT_DENIED",
                    target_type="DOCUMENT",
                    target_id=document.id,
                    metadata={
                        "recipient_id": recipient.id,
                        "reason": "Invalid permission recipient"
                    }
                )

                messages.error(
                    request,
                    "Permission cannot be granted to this user."
                )

            else:

                with transaction.atomic():

                    permission, created = (
                        DocumentPermission.objects.select_for_update()
                        .get_or_create(
                            document=document,
                            user=recipient,
                            permission=permission_type,
                            defaults={"is_active": True}
                        )
                    )

                    if created:
                        action = "PERMISSION_GRANTED"

                    elif not permission.is_active:

                        permission.is_active = True
                        permission.revoked_at = None

                        permission.save(
                            update_fields=["is_active", "revoked_at"]
                        )

                        action = "PERMISSION_REGRANTED"

                    else:
                        action = None

                    # Record only actual permission changes
                    if action:
                        record_event(
                            actor=request.user,
                            action=action,
                            target_type="DOCUMENT_PERMISSION",
                            target_id=permission.id,
                            metadata={
                                "document_id": document.id,
                                "recipient_id": recipient.id,
                                "permission": permission_type
                            }
                        )

                if action:
                    messages.success(
                        request,
                        "Document permission granted successfully."
                    )
                else:
                    messages.info(
                        request,
                        "This user already has the requested permission."
                    )

                return redirect(
                    "manage_permissions",
                    document_id=document.id
                )

    else:
        form = GrantPermissionForm()

    return render(
        request,
        "documents/grant_permission.html",
        {
            "form": form,
            "document": document
        }
    )


@login_required
def manage_permissions(request, document_id):

    document = get_object_or_404(
        Document,
        id=document_id,
        owner=request.user
    )

    permissions = document.permissions.select_related(
        "user"
    ).order_by("-granted_at")

    return render(
        request,
        "documents/manage_permissions.html",
        {
            "document": document,
            "permissions": permissions
        }
    )


@login_required
@require_POST
def revoke_permission(request, permission_id):

    with transaction.atomic():

        permission = get_object_or_404(
            DocumentPermission.objects.select_for_update().select_related(
                "document"
            ),
            id=permission_id,
            document__owner=request.user,
            is_active=True
        )

        permission.is_active = False
        permission.revoked_at = timezone.now()

        permission.save(
            update_fields=["is_active", "revoked_at"]
        )

        # Record revocation in the audit trail
        record_event(
            actor=request.user,
            action="PERMISSION_REVOKED",
            target_type="DOCUMENT_PERMISSION",
            target_id=permission.id,
            metadata={
                "document_id": permission.document_id,
                "recipient_id": permission.user_id,
                "permission": permission.permission
            }
        )

    messages.success(
        request,
        "Permission revoked successfully."
    )

    return redirect(
        "manage_permissions",
        document_id=permission.document_id
    )