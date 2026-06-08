from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsManagerOrAdmin

from .services import benchmark_dashboard_cache, get_dashboard_stats, get_monthly_finance


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        return Response({"success": True, "data": get_dashboard_stats()})


class MonthlyFinanceView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        return Response({"success": True, "data": get_monthly_finance()})


class CacheBenchmarkView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        return Response({"success": True, "data": benchmark_dashboard_cache()})
