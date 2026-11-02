from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        ('TrustVault Role', {'fields': ('role',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('TrustVault Role', {'fields': ('role',)}),
    )

    list_display = (
        'username',
        'email',
        'role',
        'is_active',
        'is_staff'
    )