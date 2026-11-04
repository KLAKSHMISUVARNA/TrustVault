from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView
from accounts.views import register_view, dashboard_view, logout_view
from audit.views import admin_audit_dashboard  

urlpatterns = [
    path('admin-portal/', admin.site.urls),
    
    # Secure Authentication Route Parameters
    path('accounts/login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/register/', register_view, name='register'),
    path('accounts/dashboard/', dashboard_view, name='dashboard'),
    path('accounts/logout/', logout_view, name='logout'),
    
    # Custom Application Routing Hooks
    path('', include('documents.urls')),
    path('admin/audit-logs/', admin_audit_dashboard, name='admin_audit_dashboard'),
]
