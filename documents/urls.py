from django.urls import path
from . import views

urlpatterns = [

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