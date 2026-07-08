from rest_framework import serializers

from apps.accounts.models import Role, User
from apps.accounts.serializers import UserSerializer
from common.rbac import Perm
from common.rbac.checker import PermissionChecker

from .models import Department, Employee, Position


class DepartmentSerializer(serializers.ModelSerializer):
    employees_count = serializers.IntegerField(source="employees.count", read_only=True)
    positions_count = serializers.IntegerField(source="positions.count", read_only=True)
    manager_name = serializers.SerializerMethodField()
    manager_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Department
        fields = (
            "id",
            "name",
            "description",
            "manager",
            "manager_id",
            "manager_name",
            "is_active",
            "employees_count",
            "positions_count",
            "created_at",
        )
        read_only_fields = ("id", "created_at", "manager", "manager_name", "manager_id")

    def get_manager_name(self, obj):
        return str(obj.manager) if obj.manager else None


class DepartmentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "name", "description", "is_active")
        read_only_fields = ("id",)


class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    employees_count = serializers.IntegerField(source="employees.count", read_only=True)

    class Meta:
        model = Position
        fields = (
            "id",
            "title",
            "department",
            "department_name",
            "base_salary",
            "employees_count",
            "is_active",
        )
        read_only_fields = ("id",)


class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    position_title = serializers.CharField(source="position.title", read_only=True)
    manager_name = serializers.SerializerMethodField()
    salary = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = (
            "id",
            "user",
            "employee_id",
            "department",
            "department_name",
            "position",
            "position_title",
            "hire_date",
            "salary",
            "manager",
            "manager_name",
            "is_active",
            "is_blocked",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def get_manager_name(self, obj):
        return str(obj.manager) if obj.manager else None

    def get_salary(self, obj):
        request = self.context.get("request")
        if request and PermissionChecker(request.user).has(Perm.SYSTEM_MANAGE):
            return str(obj.salary)
        if (
            request
            and PermissionChecker(request.user).has(Perm.EMPLOYEES_VIEW_DEPARTMENT)
            and hasattr(request.user, "employee_profile")
            and request.user.employee_profile.department_id == obj.department_id
        ):
            return None
        return None

    def get_is_blocked(self, obj):
        return not obj.user.is_active


class EmployeeDetailSerializer(EmployeeSerializer):
    task_summary = serializers.SerializerMethodField()
    recent_tasks = serializers.SerializerMethodField()
    workload = serializers.SerializerMethodField()

    class Meta(EmployeeSerializer.Meta):
        fields = EmployeeSerializer.Meta.fields + ("task_summary", "recent_tasks", "workload")

    def get_task_summary(self, obj):
        tasks = obj.tasks.all()
        total = tasks.count()
        completed = tasks.filter(status__in=["done", "approved"]).count()
        from django.utils import timezone

        overdue = tasks.filter(
            deadline__lt=timezone.now(),
            status__in=["assigned", "in_progress", "done", "rejected"],
        ).count()
        return {
            "total": total,
            "assigned": tasks.filter(status="assigned").count(),
            "in_progress": tasks.filter(status="in_progress").count(),
            "done": completed,
            "approved": tasks.filter(status="approved").count(),
            "overdue": overdue,
            "completion_rate": round(completed * 100 / total, 1) if total else 0,
        }

    def get_recent_tasks(self, obj):
        return [
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "status_display": task.get_status_display(),
                "priority": task.priority,
                "deadline": task.deadline,
                "progress": task.progress,
            }
            for task in obj.tasks.order_by("-created_at")[:6]
        ]

    def get_workload(self, obj):
        active = obj.tasks.filter(status__in=["assigned", "in_progress"]).count()
        return {"active_tasks": active, "status": "busy" if active >= 3 else "normal"}


class EmployeeCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    employee_id = serializers.CharField(max_length=32)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.filter(is_active=True))
    position = serializers.PrimaryKeyRelatedField(queryset=Position.objects.filter(is_active=True))
    hire_date = serializers.DateField()
    salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    manager = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        from django.contrib.auth.password_validation import validate_password

        validate_password(attrs["password"])
        position = attrs["position"]
        if position.department_id != attrs["department"].id:
            raise serializers.ValidationError(
                {"position": "Лауазым таңдалған бөлімге тиесілі емес."}
            )
        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError({"username": "Бұл логин бос емес."})
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "Бұл email тіркелген."})
        if Employee.objects.filter(employee_id=attrs["employee_id"]).exists():
            raise serializers.ValidationError({"employee_id": "Бұл ID қолданылып тұр."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user_fields = {
            "username": validated_data.pop("username"),
            "email": validated_data.pop("email"),
            "first_name": validated_data.pop("first_name", ""),
            "last_name": validated_data.pop("last_name", ""),
            "role": Role.EMPLOYEE,
        }
        user = User(**user_fields)
        user.set_password(password)
        user.save()

        department = validated_data["department"]
        manager = validated_data.get("manager")
        if not manager:
            manager = (
                Employee.objects.filter(
                    department=department,
                    user__role=Role.MANAGER,
                    is_active=True,
                ).first()
                or department.manager
            )
        validated_data["manager"] = manager
        return Employee.objects.create(user=user, **validated_data)


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False, allow_blank=True, write_only=True)
    last_name = serializers.CharField(required=False, allow_blank=True, write_only=True)
    email = serializers.EmailField(required=False, write_only=True)
    phone = serializers.CharField(required=False, allow_blank=True, write_only=True)
    position = serializers.PrimaryKeyRelatedField(
        queryset=Position.objects.filter(is_active=True),
        required=False,
    )

    class Meta:
        model = Employee
        fields = (
            "position",
            "salary",
            "hire_date",
            "first_name",
            "last_name",
            "email",
            "phone",
        )

    def validate_position(self, value):
        if value.department_id != self.instance.department_id:
            raise serializers.ValidationError("Лауазым тек ағымдағы бөлімге тиесілі болуы керек.")
        return value

    def update(self, instance, validated_data):
        user_fields = {}
        for field in ("first_name", "last_name", "email", "phone"):
            if field in validated_data:
                user_fields[field] = validated_data.pop(field)
        if user_fields:
            for key, val in user_fields.items():
                setattr(instance.user, key, val)
            instance.user.save(update_fields=list(user_fields.keys()) + ["updated_at"])
        return super().update(instance, validated_data)


class PromoteManagerSerializer(serializers.Serializer):
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.filter(is_active=True))


class TransferEmployeeSerializer(serializers.Serializer):
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.filter(is_active=True))
    position = serializers.PrimaryKeyRelatedField(queryset=Position.objects.filter(is_active=True))

    def validate(self, attrs):
        if attrs["position"].department_id != attrs["department"].id:
            raise serializers.ValidationError(
                {"position": "Лауазым таңдалған бөлімге тиесілі емес."}
            )
        return attrs


class AssignDepartmentManagerSerializer(serializers.Serializer):
    manager = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
