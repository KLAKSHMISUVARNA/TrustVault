from django.urls import path
from . import views

urlpatterns = [
    path(
        "",
        views.document_list,
        name="document_list"
    ),

    path(
        "upload/",
        views.upload_document,
        name="upload_document"
    ),

    path(
        "<int:document_id>/download/",
        views.download_document,
        name="download_document"
    ),

    path(
        "<int:document_id>/grant/",
        views.grant_permission,
        name="grant_permission"
    ),

    path(
        "<int:document_id>/permissions/",
        views.manage_permissions,
        name="manage_permissions"
    ),

    path(
        "permissions/<int:permission_id>/revoke/",
        views.revoke_permission,
        name="revoke_permission"
    ),
]