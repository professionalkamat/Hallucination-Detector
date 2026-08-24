from rest_framework_simplejwt.views import TokenRefreshView
from django.urls import path
from .views import RegisterView, LoginView 

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
]