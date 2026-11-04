from django import forms
from accounts.models import User
from .models import DocumentPermission
from .models import Document


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "description", "category", "file"]

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        if not uploaded_file:
            raise forms.ValidationError("No file asset was transmitted.")

        # Rejection parameters for empty data structures (0 bytes)
        if uploaded_file.size == 0:
            raise forms.ValidationError("Empty files are not allowed.")

        # Upper bound restriction checking parameters (10 MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Maximum permitted file size threshold is 10 MB.")

        return uploaded_file

class GrantPermissionForm(forms.ModelForm):

    class Meta:
        model = DocumentPermission
        fields = ["user", "permission"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["user"].queryset = User.objects.filter(
            is_active=True
        ).exclude(role="ADMIN")