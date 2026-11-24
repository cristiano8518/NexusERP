from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .audit_models import AuditLog
from .models import Role, SecurityLog, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone",
            "avatar",
            "date_joined",
        )
        read_only_fields = ("id", "role", "date_joined")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Парольдер сәйкес келмейді."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data, role=Role.EMPLOYEE)
        user.set_password(password)
        user.save()
        return user


class SecurityLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default=None)

    class Meta:
        model = SecurityLog
        fields = ("id", "username", "event_type", "ip_address", "metadata", "created_at")


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.username", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "actor_name",
            "action",
            "resource_type",
            "resource_id",
            "message",
            "changes",
            "ip_address",
            "created_at",
        )
