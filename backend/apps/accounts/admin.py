from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import reverse
from django.utils.html import format_html

from .models import SecurityLog, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "is_active",
        "is_staff",
        "date_joined",
        "admin_actions",
    )
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)
    list_per_page = 25
    actions = ["activate_users", "deactivate_users"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("NexusERP", {"fields": ("role", "phone", "avatar")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("NexusERP", {"fields": ("role", "email")}),
    )

    @admin.display(description="Әрекеттер")
    def admin_actions(self, obj):
        change_url = reverse("admin:accounts_user_change", args=[obj.pk])
        delete_url = reverse("admin:accounts_user_delete", args=[obj.pk])
        return format_html(
            '<span class="nexuserp-actions">'
            '<a href="{}">Өңдеу</a> '
            '<a class="deletelink" href="{}">Өшіру</a>'
            "</span>",
            change_url,
            delete_url,
        )

    @admin.action(description="Белсенді ету")
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} пайдаланушы белсенді етілді.", messages.SUCCESS)

    @admin.action(description="Белсенділікті өшіру")
    def deactivate_users(self, request, queryset):
        if queryset.filter(id=request.user.id).exists():
            self.message_user(request, "Өз аккаунтыңызды өшіре алмайсыз.", messages.ERROR)
            return
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} пайдаланушы өшірілді.", messages.WARNING)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.pk == request.user.pk:
            return False
        return super().has_delete_permission(request, obj)

    def delete_model(self, request, obj):
        if obj.pk == request.user.pk:
            self.message_user(request, "Өз аккаунтыңызды өшіре алмайсыз.", messages.ERROR)
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        if queryset.filter(pk=request.user.pk).exists():
            self.message_user(
                request,
                "Тізімнен өз аккаунтыңызды алып, қайта көріңіз.",
                messages.ERROR,
            )
            return
        count = queryset.count()
        super().delete_queryset(request, queryset)
        self.message_user(request, f"{count} пайдаланушы өшірілді.", messages.SUCCESS)


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "user", "ip_address", "created_at", "admin_actions")
    list_filter = ("event_type", "created_at")
    search_fields = ("user__username", "ip_address")
    readonly_fields = ("user", "event_type", "ip_address", "user_agent", "metadata", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="")
    def admin_actions(self, obj):
        delete_url = reverse("admin:accounts_securitylog_delete", args=[obj.pk])
        return format_html('<a class="deletelink" href="{}">Өшіру</a>', delete_url)
