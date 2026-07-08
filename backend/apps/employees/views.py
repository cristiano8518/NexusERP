from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.rbac import Perm
from common.rbac.checker import PermissionChecker
from common.rbac.drf_permissions import require_any_permission, require_permission
from common.rbac.scope import scope_queryset

from .models import Department, Employee, Position
from .serializers import (
    AssignDepartmentManagerSerializer,
    DepartmentSerializer,
    DepartmentWriteSerializer,
    EmployeeCreateSerializer,
    EmployeeDetailSerializer,
    EmployeeSerializer,
    EmployeeUpdateSerializer,
    PositionSerializer,
    PromoteManagerSerializer,
    TransferEmployeeSerializer,
)
from .services import (
    HRPermissionError,
    HRValidationError,
    assign_department_manager,
    block_employee,
    demote_from_manager,
    promote_to_manager,
    transfer_employee,
    unblock_employee,
)


def _forbidden(message="Недостаточно прав доступа."):
    raise PermissionDenied(message)


def _handle_hr_error(exc):
    if isinstance(exc, HRPermissionError):
        raise PermissionDenied(str(exc)) from exc
    if isinstance(exc, HRValidationError):
        raise ValidationError({"detail": str(exc)}) from exc
    raise exc


class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]

    def get_queryset(self):
        return scope_queryset(
            Department.objects.select_related("manager", "manager__user").all(),
            self.request.user,
            "departments",
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return DepartmentWriteSerializer
        return DepartmentSerializer

    def get_permissions(self):
        if self.action in ("create",):
            return [IsAuthenticated(), require_permission(Perm.DEPARTMENTS_CREATE)()]
        if self.action in ("update", "partial_update"):
            return [IsAuthenticated(), require_permission(Perm.DEPARTMENTS_UPDATE)()]
        if self.action == "destroy":
            return [IsAuthenticated(), require_permission(Perm.DEPARTMENTS_DELETE)()]
        if self.action == "assign_manager":
            return [IsAuthenticated(), require_permission(Perm.DEPARTMENTS_ASSIGN_MANAGER)()]
        if self.action in ("list", "retrieve"):
            return [
                IsAuthenticated(),
                require_any_permission(Perm.DEPARTMENTS_VIEW_ALL, Perm.DEPARTMENTS_VIEW_OWN)(),
            ]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        checker = PermissionChecker(request.user)
        if not checker.has_any(Perm.DEPARTMENTS_VIEW_ALL, Perm.DEPARTMENTS_VIEW_OWN):
            _forbidden()
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        checker = PermissionChecker(request.user)
        if not checker.has_any(Perm.DEPARTMENTS_VIEW_ALL, Perm.DEPARTMENTS_VIEW_OWN):
            _forbidden()
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.DEPARTMENTS_CREATE):
            _forbidden()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.DEPARTMENTS_UPDATE):
            _forbidden()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.DEPARTMENTS_UPDATE):
            _forbidden()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.DEPARTMENTS_DELETE):
            _forbidden()
        department = self.get_object()
        if department.employees.filter(is_active=True).exists():
            raise ValidationError({"detail": "Бөлімде белсенді қызметкерлер бар. Алдымен оларды ауыстырыңыз."})
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="assign-manager")
    def assign_manager(self, request, pk=None):
        department = self.get_object()
        serializer = AssignDepartmentManagerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            assign_department_manager(
                actor=request.user,
                department=department,
                manager=serializer.validated_data.get("manager"),
            )
        except (HRPermissionError, HRValidationError) as exc:
            _handle_hr_error(exc)
        department.refresh_from_db()
        return Response(
            {"success": True, "department": DepartmentSerializer(department).data}
        )


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.select_related("department")
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["title"]

    def get_queryset(self):
        return scope_queryset(
            Position.objects.select_related("department"),
            self.request.user,
            "positions",
        )

    def get_permissions(self):
        if self.action in ("create",):
            return [IsAuthenticated(), require_permission(Perm.POSITIONS_CREATE)()]
        if self.action in ("update", "partial_update"):
            return [IsAuthenticated(), require_permission(Perm.POSITIONS_UPDATE)()]
        if self.action == "destroy":
            return [IsAuthenticated(), require_permission(Perm.POSITIONS_DELETE)()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        checker = PermissionChecker(request.user)
        if not checker.has_any(Perm.POSITIONS_VIEW_ALL, Perm.POSITIONS_VIEW_OWN):
            _forbidden()
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        checker = PermissionChecker(request.user)
        if not checker.has_any(Perm.POSITIONS_VIEW_ALL, Perm.POSITIONS_VIEW_OWN):
            _forbidden()
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.POSITIONS_CREATE):
            _forbidden()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.POSITIONS_UPDATE):
            _forbidden()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.POSITIONS_UPDATE):
            _forbidden()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.POSITIONS_DELETE):
            _forbidden()
        return super().destroy(request, *args, **kwargs)


class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    search_fields = ["employee_id", "user__username", "user__first_name"]

    def get_queryset(self):
        return scope_queryset(
            Employee.objects.select_related("user", "department", "position", "manager"),
            self.request.user,
            "employees",
        )

    def get_serializer_class(self):
        if self.action == "create":
            return EmployeeCreateSerializer
        if self.action == "retrieve":
            return EmployeeDetailSerializer
        if self.action in ("update", "partial_update"):
            return EmployeeUpdateSerializer
        return EmployeeSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), require_permission(Perm.EMPLOYEES_CREATE)()]
        if self.action == "destroy":
            return [IsAuthenticated(), require_permission(Perm.EMPLOYEES_DELETE)()]
        if self.action in ("update", "partial_update"):
            return [IsAuthenticated(), require_permission(Perm.EMPLOYEES_UPDATE)()]
        if self.action in ("promote", "demote", "block", "unblock", "transfer"):
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        checker = PermissionChecker(request.user)
        if not checker.has_any(Perm.EMPLOYEES_VIEW_ALL, Perm.EMPLOYEES_VIEW_DEPARTMENT):
            _forbidden()
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        checker = PermissionChecker(request.user)
        if not checker.has_any(Perm.EMPLOYEES_VIEW_ALL, Perm.EMPLOYEES_VIEW_DEPARTMENT):
            _forbidden()
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.EMPLOYEES_CREATE):
            _forbidden()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        return Response(
            {"success": True, "employee": EmployeeSerializer(employee, context={"request": request}).data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.EMPLOYEES_UPDATE):
            _forbidden()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.EMPLOYEES_UPDATE):
            _forbidden()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.EMPLOYEES_DELETE):
            _forbidden()
        employee = self.get_object()
        if employee.user.role == "admin":
            raise ValidationError({"detail": "Директорды жоюға болмайды."})
        user = employee.user
        self.perform_destroy(employee)
        user.delete()
        return Response({"success": True, "detail": "Қызметкер жойылды."})

    @action(detail=True, methods=["post"])
    def promote(self, request, pk=None):
        if not PermissionChecker(request.user).has(Perm.EMPLOYEES_PROMOTE_MANAGER):
            _forbidden()
        employee = self.get_object()
        serializer = PromoteManagerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            promote_to_manager(
                actor=request.user,
                employee=employee,
                department=serializer.validated_data["department"],
            )
        except (HRPermissionError, HRValidationError) as exc:
            _handle_hr_error(exc)
        employee.refresh_from_db()
        return Response(
            {"success": True, "employee": EmployeeSerializer(employee, context={"request": request}).data}
        )

    @action(detail=True, methods=["post"])
    def demote(self, request, pk=None):
        if not PermissionChecker(request.user).has(Perm.EMPLOYEES_DEMOTE_MANAGER):
            _forbidden()
        employee = self.get_object()
        try:
            demote_from_manager(actor=request.user, employee=employee)
        except (HRPermissionError, HRValidationError) as exc:
            _handle_hr_error(exc)
        employee.refresh_from_db()
        return Response(
            {"success": True, "employee": EmployeeSerializer(employee, context={"request": request}).data}
        )

    @action(detail=True, methods=["post"])
    def block(self, request, pk=None):
        if not PermissionChecker(request.user).has(Perm.EMPLOYEES_BLOCK):
            _forbidden()
        employee = self.get_object()
        try:
            block_employee(actor=request.user, employee=employee)
        except (HRPermissionError, HRValidationError) as exc:
            _handle_hr_error(exc)
        employee.refresh_from_db()
        return Response(
            {"success": True, "employee": EmployeeSerializer(employee, context={"request": request}).data}
        )

    @action(detail=True, methods=["post"])
    def unblock(self, request, pk=None):
        if not PermissionChecker(request.user).has(Perm.EMPLOYEES_BLOCK):
            _forbidden()
        employee = self.get_object()
        try:
            unblock_employee(actor=request.user, employee=employee)
        except (HRPermissionError, HRValidationError) as exc:
            _handle_hr_error(exc)
        employee.refresh_from_db()
        return Response(
            {"success": True, "employee": EmployeeSerializer(employee, context={"request": request}).data}
        )

    @action(detail=True, methods=["post"])
    def transfer(self, request, pk=None):
        if not PermissionChecker(request.user).has(Perm.EMPLOYEES_TRANSFER):
            _forbidden()
        employee = self.get_object()
        serializer = TransferEmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            transfer_employee(
                actor=request.user,
                employee=employee,
                department=serializer.validated_data["department"],
                position=serializer.validated_data["position"],
            )
        except (HRPermissionError, HRValidationError) as exc:
            _handle_hr_error(exc)
        employee.refresh_from_db()
        return Response(
            {"success": True, "employee": EmployeeSerializer(employee, context={"request": request}).data}
        )
