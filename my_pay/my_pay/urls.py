from django.contrib import admin
from django.urls import path, include
from feed.views import index

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index, name="index"),
    path("accounts/", include("allauth.urls")),
    path("payment/", include("payment.urls")),
]
