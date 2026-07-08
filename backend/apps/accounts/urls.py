from django.urls import path

from .views import (
    AuditLogListView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    MeView,
    RegisterView,
    SecurityLogListView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="auth-login"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("security-logs/", SecurityLogListView.as_view(), name="auth-security-logs"),
    path("audit-logs/", AuditLogListView.as_view(), name="auth-audit-logs"),
]
