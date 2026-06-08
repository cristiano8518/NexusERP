from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Department, Employee, Position


class EmployeeAdminMixin:
    @admin.display(description="Әрекеттер")
    def admin_actions(self, obj):
        change_url = reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
            args=[obj.pk],
        )
        delete_url = reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}_delete",
            args=[obj.pk],
        )
        return format_html(
            '<span class="nexuserp-actions">'
            '<a href="{}">Өңдеу</a> '
            '<a class="deletelink" href="{}">Өшіру</a>'
            "</span>",
            change_url,
            delete_url,
        )


@admin.register(Department)
class DepartmentAdmin(EmployeeAdminMixin, admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "admin_actions")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Position)
class PositionAdmin(EmployeeAdminMixin, admin.ModelAdmin):
    list_display = ("title", "department", "base_salary", "is_active", "admin_actions")
    list_filter = ("department", "is_active")
    search_fields = ("title",)


@admin.register(Employee)
class EmployeeAdmin(EmployeeAdminMixin, admin.ModelAdmin):
    list_display = (
        "employee_id",
        "user",
        "department",
        "position",
        "is_active",
        "admin_actions",
    )
    list_filter = ("department", "is_active")
    search_fields = ("employee_id", "user__username", "user__email")
    raw_id_fields = ("user", "manager")
