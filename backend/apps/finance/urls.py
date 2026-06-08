from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FinanceEntryViewSet

router = DefaultRouter()
router.register("entries", FinanceEntryViewSet, basename="finance-entry")

urlpatterns = [
    path("", include(router.urls)),
]
