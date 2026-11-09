import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, SuspiciousFileOperation
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import select_template
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from .forms import DocumentUploadForm, PermissionGrantForm
from .models import Document, DocumentPermission
from .permissions import check_document_access, can_access_document, get_client_ip
from audit.services import record_audit_event

User = get_user_model()


@login_required
@require_GET
def document_list(request):
    user = request.user

    if getattr(user, "role", None) == User.Role.ADMIN:
        base_qs = Document.objects.all()
    else:
        base_qs = Document.objects.filter(
            Q(owner=user) | Q(permissions__user=user, permissions__is_active=True)
        ).distinct()

    query = request.GET.get("q", "").strip()
    if query:
        base_qs = base_qs.filter(
            Q(title__icontains=query)
            | Q(file__icontains=query)
            | Q(owner__username__icontains=query)
        )

    documents = base_qs.select_related("owner").order_by("-created_at")

    template = select_template(["documents/document_list.html", "documents/list.html"])
    return render(
        request,
        template.template.name,
        {
            "documents": documents,
            "query": query,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def upload_document(request):
    user = request.user
    if getattr(user, "role", None) not in [User.Role.OWNER, User.Role.ADMIN]:
        raise PermissionDenied("Only document owners and administrators can upload files.")

    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data.get("file") or request.FILES.get("file")
            with transaction.atomic():
                document = form.save(commit=False)
                document.owner = user
                document.file_size = uploaded_file.size if uploaded_file else 0
                document.save()

                doc_display_name = getattr(document, "title", getattr(uploaded_file, "name", "document"))
                record_audit_event(
                    actor=user,
                    document=document,
                    action="DOCUMENT_UPLOADED",
                    details=f"Document uploaded: {doc_display_name}",
                    ip_address=get_client_ip(request),
                )

            messages.success(request, "Document uploaded successfully.")
            return redirect("document_list")
    else:
        form = DocumentUploadForm()

    template = select_template([
        "documents/document_upload.html",
        "documents/upload.html",
        "documents/document_form.html",
    ])
    return render(request, template.template.name, {"form": form})


@login_required
@require_GET
def download_document(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    check_document_access(request, document, required_level="READ")

    file_path = document.file.path
    if not os.path.abspath(file_path).startswith(os.path.abspath(str(settings.MEDIA_ROOT))):
        raise SuspiciousFileOperation("Access outside private storage boundary.")

    record_audit_event(
        actor=request.user,
        document=document,
        action="DOCUMENT_DOWNLOADED",
        details=f"Document {document.id} downloaded.",
        ip_address=get_client_ip(request),
    )

    download_name = os.path.basename(document.file.name)
    response = FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=download_name,
    )
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Security-Policy"] = "default-src 'none';"
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


@login_required
@require_GET
def manage_permissions(request, document_id):
    document = get_object_or_404(Document, pk=document_id)

    # RBAC check: only document owner or system admin can view permission summary
    if document.owner_id != request.user.id and getattr(request.user, "role", None) != User.Role.ADMIN:
        raise Http404("Document not found.")

    permissions = DocumentPermission.objects.filter(
        document=document
    ).select_related("user").order_by("-id")

    template = select_template([
        "documents/manage_permissions.html",
        "documents/permissions_summary.html",
    ])

    return render(
        request,
        template.template.name,
        {
            "document": document,
            "permissions": permissions,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def grant_permission(request, document_id):
    document = get_object_or_404(Document, pk=document_id)

    # RBAC check: only document owner or system admin can grant permissions
    if document.owner_id != request.user.id and getattr(request.user, "role", None) != User.Role.ADMIN:
        raise Http404("Document not found.")

    if request.method == "POST":
        form = PermissionGrantForm(request.POST)
        if form.is_valid():
            target_user = form.cleaned_data["user"]
            perm_type = form.cleaned_data["permission"]

            if target_user.id == document.owner_id:
                messages.warning(request, "Document owner already has full permissions.")
                return redirect("manage_permissions", document_id=document_id)

            with transaction.atomic():
                perm, created = DocumentPermission.objects.update_or_create(
                    document=document,
                    user=target_user,
                    defaults={
                        "permission": perm_type,
                        "is_active": True,
                        "revoked_at": None,
                    },
                )

                record_audit_event(
                    actor=request.user,
                    document=document,
                    action="PERMISSION_GRANTED",
                    details=f"Granted {perm_type} to user {target_user.username}",
                    ip_address=get_client_ip(request),
                )

            messages.success(request, f"Granted {perm_type} permission to {target_user.username}.")
            return redirect("manage_permissions", document_id=document_id)
        else:
            messages.error(request, "Invalid input. Please check the form fields.")
    else:
        form = PermissionGrantForm()

    template = select_template([
        "documents/grant_permission.html",
        "documents/grant_access.html",
    ])

    return render(
        request,
        template.template.name,
        {
            "document": document,
            "form": form,
        },
    )


@login_required
@require_POST
def revoke_permission(request, permission_id):
    permission = get_object_or_404(DocumentPermission, pk=permission_id)
    document = permission.document

    if document.owner_id != request.user.id and getattr(request.user, "role", None) != User.Role.ADMIN:
        raise Http404("Document not found.")

    with transaction.atomic():
        permission.is_active = False
        permission.revoked_at = timezone.now()
        permission.save()

        record_audit_event(
            actor=request.user,
            document=document,
            action="PERMISSION_REVOKED",
            details=f"Revoked permission for user {permission.user.username}",
            ip_address=get_client_ip(request),
        )

    messages.success(request, f"Revoked access for {permission.user.username}.")
    return redirect("manage_permissions", document_id=document.id)


# Function Aliases for URL routing compatibility
document_list_view = document_list
upload_document_view = upload_document
download_document_view = download_document
manage_permissions_view = manage_permissions
grant_permission_view = grant_permission
revoke_permission_view = revoke_permission