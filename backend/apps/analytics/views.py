from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsManagerOrAdmin

from .services import benchmark_dashboard_cache, get_dashboard_stats, get_monthly_finance


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        return Response({"success": True, "data": get_dashboard_stats(department_id=_department_scope(request.user))})


class MonthlyFinanceView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        return Response({"success": True, "data": get_monthly_finance(department_id=_department_scope(request.user))})


class CacheBenchmarkView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        return Response({"success": True, "data": benchmark_dashboard_cache(department_id=_department_scope(request.user))})


def _department_scope(user):
    if getattr(user, "role", None) == "manager" and hasattr(user, "employee_profile"):
        return user.employee_profile.department_id
    return None
