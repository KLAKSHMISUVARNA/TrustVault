from django import forms
from django.contrib.auth import get_user_model
from .models import Document, DocumentPermission

User = get_user_model()


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ("title", "file")
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter document title",
            }),
            "file": forms.FileInput(attrs={
                "class": "form-control",
            }),
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        if not uploaded_file:
            raise forms.ValidationError("A file must be selected for upload.")
        from .validators import validate_document_file
        validate_document_file(uploaded_file)
        return uploaded_file


class PermissionGrantForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=True,
        label="Grant Access To",
        empty_label="Select a user",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    permission = forms.ChoiceField(
        choices=[
            ("READ", "Read-Only"),
            ("EDIT", "Can Edit"),
        ],
        required=True,
        label="Permission Level",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    # Allow compatibility if POST requests send 'permission_type'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data and "permission_type" in self.data and "permission" not in self.data:
            self.data = self.data.copy()
            self.data["permission"] = self.data["permission_type"]


ShareDocumentForm = PermissionGrantForm
GrantAccessForm = PermissionGrantForm