from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


urlpatterns = [
    path('', lambda request: redirect('login')),

    path('admin/', admin.site.urls),

    path('accounts/', include('accounts.urls')),
]