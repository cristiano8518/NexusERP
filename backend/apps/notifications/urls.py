from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BulkEmailView, NotificationViewSet

router = DefaultRouter()
router.register("", NotificationViewSet, basename="notification")

urlpatterns = [
    path("bulk-email/", BulkEmailView.as_view(), name="notifications-bulk-email"),
    path("", include(router.urls)),
]
