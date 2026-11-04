from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        
        # Enforce structural role containment on the server side.
        # All public registrations are forcefully defaulted to VIEWER.
        user.role = User.Role.VIEWER

        if commit:
            user.save()

        return user
