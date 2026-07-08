from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.rbac import Perm
from common.rbac.checker import PermissionChecker

from .services import benchmark_dashboard_cache, get_dashboard_stats, get_monthly_finance, get_performance_stats


def _department_scope(user):
    checker = PermissionChecker(user)
    if checker.has(Perm.ANALYTICS_VIEW_COMPANY):
        return None
    if checker.has(Perm.ANALYTICS_VIEW_DEPARTMENT):
        return checker.department_id()
    return None


def _require_analytics(user):
    checker = PermissionChecker(user)
    if not checker.has_any(Perm.ANALYTICS_VIEW_COMPANY, Perm.ANALYTICS_VIEW_DEPARTMENT):
        raise PermissionDenied("Недостаточно прав доступа.")


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_analytics(request.user)
        return Response(
            {"success": True, "data": get_dashboard_stats(department_id=_department_scope(request.user))}
        )


class MonthlyFinanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_analytics(request.user)
        return Response(
            {"success": True, "data": get_monthly_finance(department_id=_department_scope(request.user))}
        )


class CacheBenchmarkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_analytics(request.user)
        return Response(
            {"success": True, "data": benchmark_dashboard_cache(department_id=_department_scope(request.user))}
        )


class PerformanceStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        checker = PermissionChecker(request.user)
        if checker.has(Perm.ANALYTICS_VIEW_PERFORMANCE):
            dept_id = _department_scope(request.user)
        elif checker.has(Perm.ANALYTICS_VIEW_DEPARTMENT):
            dept_id = checker.department_id()
        else:
            raise PermissionDenied("Недостаточно прав доступа.")
        return Response(
            {"success": True, "data": get_performance_stats(department_id=dept_id)}
        )
