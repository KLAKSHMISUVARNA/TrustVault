from django import forms
from accounts.models import User
from .models import DocumentPermission


class GrantPermissionForm(forms.ModelForm):

    class Meta:
        model = DocumentPermission
        fields = ["user", "permission"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["user"].queryset = User.objects.filter(
            is_active=True
        ).exclude(role="ADMIN")