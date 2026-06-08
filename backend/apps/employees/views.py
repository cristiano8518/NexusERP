from rest_framework import status, viewsets
from rest_framework.response import Response

from common.permissions import IsAdminRole, IsManagerOrAdmin

from .models import Department, Employee, Position
from .serializers import (
    DepartmentSerializer,
    EmployeeCreateSerializer,
    EmployeeDetailSerializer,
    EmployeeSerializer,
    PositionSerializer,
)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsManagerOrAdmin]
    search_fields = ["name"]


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.select_related("department")
    serializer_class = PositionSerializer
    permission_classes = [IsManagerOrAdmin]
    search_fields = ["title"]


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related("user", "department", "position")
    search_fields = ["employee_id", "user__username", "user__first_name"]

    def get_serializer_class(self):
        if self.action == "create":
            return EmployeeCreateSerializer
        if self.action == "retrieve":
            return EmployeeDetailSerializer
        return EmployeeSerializer

    def get_permissions(self):
        if self.action in ("create", "destroy", "update", "partial_update"):
            return [IsAdminRole()]
        return [IsManagerOrAdmin()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        return Response(
            {"success": True, "employee": EmployeeSerializer(employee).data},
            status=201,
        )
