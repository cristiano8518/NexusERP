from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import Role, User
from apps.accounts.serializers import UserSerializer

from .models import Department, Employee, Position


class DepartmentSerializer(serializers.ModelSerializer):
    employees_count = serializers.IntegerField(source="employees.count", read_only=True)
    positions_count = serializers.IntegerField(source="positions.count", read_only=True)

    class Meta:
        model = Department
        fields = (
            "id",
            "name",
            "description",
            "is_active",
            "employees_count",
            "positions_count",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


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
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def get_manager_name(self, obj):
        return str(obj.manager) if obj.manager else None

    def get_salary(self, obj):
        request = self.context.get("request")
        if request and request.user.role == Role.ADMIN:
            return str(obj.salary)
        return None


class EmployeeDetailSerializer(EmployeeSerializer):
    task_summary = serializers.SerializerMethodField()
    recent_tasks = serializers.SerializerMethodField()

    class Meta(EmployeeSerializer.Meta):
        fields = EmployeeSerializer.Meta.fields + ("task_summary", "recent_tasks")

    def get_task_summary(self, obj):
        tasks = obj.tasks.all()
        total = tasks.count()
        completed = tasks.filter(status__in=["done", "approved"]).count()
        return {
            "total": total,
            "assigned": tasks.filter(status="assigned").count(),
            "in_progress": tasks.filter(status="in_progress").count(),
            "done": completed,
            "approved": tasks.filter(status="approved").count(),
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


class EmployeeCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=Role.choices, default=Role.EMPLOYEE)
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
        role = validated_data.pop("role")
        password = validated_data.pop("password")
        user_fields = {
            "username": validated_data.pop("username"),
            "email": validated_data.pop("email"),
            "first_name": validated_data.pop("first_name", ""),
            "last_name": validated_data.pop("last_name", ""),
            "role": role,
        }
        user = User(**user_fields)
        user.set_password(password)
        user.save()

        return Employee.objects.create(user=user, **validated_data)
