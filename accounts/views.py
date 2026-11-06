from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from .forms import RegistrationForm

def register_view(request):
  if request.user.is_authenticated:
    return redirect("document_list")

  if request.method == "POST":
    form = RegistrationForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(
          request,
          "Account created successfully as a Viewer. Please log in.",
      )
      return redirect("login")
  else:
    form = RegistrationForm()

  return render(request, "accounts/register.html", {"form": form})
@login_required
def dashboard_view(request):

    return render(request, "accounts/dashboard.html")


def logout_view(request):

    if request.method == "POST":
        logout(request)
        return redirect("login")

    return redirect("dashboard")