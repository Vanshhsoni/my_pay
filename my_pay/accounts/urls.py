from django.urls import path
from django.shortcuts import redirect

def google_login_redirect(request):
    return redirect('/accounts/google/login/')

urlpatterns = [
    path("login/", google_login_redirect, name="login"),   # 👈 force direct google
]