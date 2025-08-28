# payment/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_page, name='payment_page'),
    path('verify/', views.verify_payment, name='verify_payment'),
    path('success/', views.success_page, name='success_page'),
    path('failure/', views.failure_page, name='failure_page'),
]