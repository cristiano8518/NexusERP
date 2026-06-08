from django.urls import path

from .views import CacheBenchmarkView, DashboardStatsView, MonthlyFinanceView

urlpatterns = [
    path("dashboard/", DashboardStatsView.as_view(), name="analytics-dashboard"),
    path("monthly-finance/", MonthlyFinanceView.as_view(), name="analytics-monthly-finance"),
    path("cache-benchmark/", CacheBenchmarkView.as_view(), name="analytics-cache-benchmark"),
]
