from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BulkEmailView, NotificationPreferenceView, NotificationViewSet

router = DefaultRouter()
router.register("", NotificationViewSet, basename="notification")

urlpatterns = [
    path("bulk-email/", BulkEmailView.as_view(), name="notifications-bulk-email"),
    path("preferences/", NotificationPreferenceView.as_view(), name="notifications-preferences"),
    path("", include(router.urls)),
]
