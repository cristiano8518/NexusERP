"""HR operations — promotions, demotions, blocking, transfers."""

from django.db import transaction

from apps.accounts.models import Role, User
from common.audit import log_audit_event
from common.rbac import Perm
from common.rbac.checker import PermissionChecker

from .models import Department, Employee, Position


class HRPermissionError(PermissionError):
    pass


class HRValidationError(ValueError):
    pass


def _require(user, permission: str) -> PermissionChecker:
    checker = PermissionChecker(user)
    if not checker.has(permission):
        raise HRPermissionError("Рұқсат жеткіліксіз.")
    return checker


@transaction.atomic
def promote_to_manager(*, actor: User, employee: Employee, department: Department) -> Employee:
    _require(actor, Perm.EMPLOYEES_PROMOTE_MANAGER)

    if employee.user.role == Role.ADMIN:
        raise HRValidationError("Директорды менеджерге ауыстыруға болмайды.")

    if employee.user.role == Role.MANAGER:
        raise HRValidationError("Қызметкер қазірдің өзінде менеджер.")

    if not department.is_active:
        raise HRValidationError("Бөлім белсенді емес.")

    if employee.department_id != department.id:
        raise HRValidationError(
            "Менеджер ретінде тағайындау үшін қызметкер таңдалған бөлімде болуы керек. "
            "Алдымен бөлімді ауыстырыңыз."
        )

    if department.manager_id and department.manager_id != employee.id:
        old_manager = department.manager
        old_manager.user.role = Role.EMPLOYEE
        old_manager.user.save(update_fields=["role", "updated_at"])
        Employee.objects.filter(manager=old_manager).update(manager=employee)

    employee.user.role = Role.MANAGER
    employee.user.save(update_fields=["role", "updated_at"])
    employee.manager = None
    employee.save(update_fields=["manager", "updated_at"])

    department.manager = employee
    department.save(update_fields=["manager"])

    Employee.objects.filter(department=department, manager__isnull=True).exclude(
        id=employee.id
    ).update(manager=employee)

    log_audit_event(
        actor=actor,
        action="promote",
        resource_type="employee",
        resource_id=employee.id,
        message=f"{employee} → менеджер ({department.name})",
        changes={"role": "manager", "department_id": department.id},
    )

    return employee


@transaction.atomic
def _demote_manager_internal(*, employee: Employee) -> Employee:
    """Demote manager to employee without a separate permission check (internal HR ops)."""
    if employee.user.role != Role.MANAGER:
        return employee

    department = Department.objects.filter(manager=employee).first()
    if department:
        department.manager = None
        department.save(update_fields=["manager"])

    employee.user.role = Role.EMPLOYEE
    employee.user.save(update_fields=["role", "updated_at"])

    new_head = (
        Employee.objects.filter(
            department=employee.department,
            user__role=Role.ADMIN,
            is_active=True,
        )
        .select_related("user")
        .first()
    )
    if not new_head:
        new_head = (
            Employee.objects.filter(
                department=employee.department,
                is_active=True,
            )
            .exclude(id=employee.id)
            .order_by("hire_date")
            .first()
        )
    Employee.objects.filter(manager=employee).update(manager=new_head)
    if new_head:
        employee.manager = new_head
        employee.save(update_fields=["manager", "updated_at"])

    return employee


@transaction.atomic
def demote_from_manager(*, actor: User, employee: Employee) -> Employee:
    _require(actor, Perm.EMPLOYEES_DEMOTE_MANAGER)

    if employee.user.role != Role.MANAGER:
        raise HRValidationError("Тек менеджерді қызметкерге түсіруге болады.")

    employee = _demote_manager_internal(employee=employee)

    log_audit_event(
        actor=actor,
        action="demote",
        resource_type="employee",
        resource_id=employee.id,
        message=f"{employee} → қызметкер",
    )
    return employee


@transaction.atomic
def block_employee(*, actor: User, employee: Employee) -> Employee:
    _require(actor, Perm.EMPLOYEES_BLOCK)

    if employee.user.role == Role.ADMIN:
        raise HRValidationError("Директорды блоктауға болмайды.")

    employee.is_active = False
    employee.user.is_active = False
    employee.save(update_fields=["is_active", "updated_at"])
    employee.user.save(update_fields=["is_active", "updated_at"])

    if employee.user.role == Role.MANAGER:
        Department.objects.filter(manager=employee).update(manager=None)

    log_audit_event(
        actor=actor,
        action="block",
        resource_type="employee",
        resource_id=employee.id,
        message=f"{employee} блокталды",
    )
    return employee


@transaction.atomic
def unblock_employee(*, actor: User, employee: Employee) -> Employee:
    _require(actor, Perm.EMPLOYEES_BLOCK)

    employee.is_active = True
    employee.user.is_active = True
    employee.save(update_fields=["is_active", "updated_at"])
    employee.user.save(update_fields=["is_active", "updated_at"])
    log_audit_event(
        actor=actor,
        action="unblock",
        resource_type="employee",
        resource_id=employee.id,
        message=f"{employee} блоктан шығарылды",
    )
    return employee


@transaction.atomic
def transfer_employee(
    *,
    actor: User,
    employee: Employee,
    department: Department,
    position: Position,
) -> Employee:
    _require(actor, Perm.EMPLOYEES_TRANSFER)

    if employee.user.role == Role.ADMIN:
        raise HRValidationError("Директорды басқа бөлімге ауыстыруға болмайды.")

    if employee.user.role == Role.MANAGER:
        raise HRValidationError(
            "Менеджерді бөлім ауыстыру алдында қызметкерге түсіріңіз немесе "
            "жаңа бөлімде менеджер ретінде қайта тағайындаңыз."
        )

    if position.department_id != department.id:
        raise HRValidationError("Лауазым таңдалған бөлімге тиесілі емес.")

    if not department.is_active or not position.is_active:
        raise HRValidationError("Бөлім немесе лауазым белсенді емес.")

    new_manager = (
        Employee.objects.filter(
            department=department,
            user__role=Role.MANAGER,
            is_active=True,
        )
        .select_related("user")
        .first()
    )
    if not new_manager and department.manager_id:
        new_manager = department.manager

    employee.department = department
    employee.position = position
    employee.manager = new_manager
    employee.save(update_fields=["department", "position", "manager", "updated_at"])
    log_audit_event(
        actor=actor,
        action="transfer",
        resource_type="employee",
        resource_id=employee.id,
        message=f"{employee} → {department.name}",
        changes={"department_id": department.id, "position_id": position.id},
    )
    return employee


@transaction.atomic
def assign_department_manager(
    *, actor: User, department: Department, manager: Employee | None
) -> Department:
    _require(actor, Perm.DEPARTMENTS_ASSIGN_MANAGER)

    if manager:
        if manager.department_id != department.id:
            raise HRValidationError("Менеджер осы бөлімнің қызметкері болуы керек.")
        if manager.user.role == Role.ADMIN:
            raise HRValidationError("Директорды бөлім менеджері ретінде тағайындауға болмайды.")
        if department.manager_id == manager.id and manager.user.role == Role.MANAGER:
            return department

        if department.manager_id and department.manager_id != manager.id:
            old_manager = department.manager
            _demote_manager_internal(employee=old_manager)
            log_audit_event(
                actor=actor,
                action="demote",
                resource_type="employee",
                resource_id=old_manager.id,
                message=f"{old_manager} → қызметкер (жаңа менеджер тағайындалды)",
            )

        promote_to_manager(actor=actor, employee=manager, department=department)
    else:
        if department.manager:
            old_manager = department.manager
            _demote_manager_internal(employee=old_manager)
            log_audit_event(
                actor=actor,
                action="demote",
                resource_type="employee",
                resource_id=old_manager.id,
                message=f"{old_manager} → қызметкер (бөлім менеджері постынан алынды)",
            )
        department.manager = None
        department.save(update_fields=["manager"])

    department.refresh_from_db()
    return department
