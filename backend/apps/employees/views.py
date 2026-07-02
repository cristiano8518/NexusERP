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

    def get_queryset(self):
        user = self.request.user
        qs = Department.objects.all()
        if getattr(user, "role", None) == "admin":
            return qs
        if getattr(user, "role", None) == "manager" and hasattr(user, "employee_profile"):
            return qs.filter(id=user.employee_profile.department_id)
        return qs.none()


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.select_related("department")
    serializer_class = PositionSerializer
    permission_classes = [IsManagerOrAdmin]
    search_fields = ["title"]

    def get_queryset(self):
        user = self.request.user
        qs = Position.objects.select_related("department")
        if getattr(user, "role", None) == "admin":
            return qs
        if getattr(user, "role", None) == "manager" and hasattr(user, "employee_profile"):
            return qs.filter(department_id=user.employee_profile.department_id)
        return qs.none()


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related("user", "department", "position")
    search_fields = ["employee_id", "user__username", "user__first_name"]

    def get_queryset(self):
        user = self.request.user
        qs = Employee.objects.select_related("user", "department", "position", "manager")
        if getattr(user, "role", None) == "admin":
            return qs
        if getattr(user, "role", None) == "manager" and hasattr(user, "employee_profile"):
            return qs.filter(department_id=user.employee_profile.department_id)
        return qs.none()

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
