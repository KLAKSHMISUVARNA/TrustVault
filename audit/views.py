from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import AuditEvent

@login_required
def admin_audit_dashboard(request):
    # Enforce strict server-side evaluation bounds matching requirements
    if request.user.role != 'ADMIN':
        return HttpResponseForbidden("Access evaluation mapping constraints failed to resolve execution privileges.")
        
    events = AuditEvent.objects.all().order_by('-created_at')
    return render(request, 'audit/admin_dashboard.html', {'audit_events': events})
