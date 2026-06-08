from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import FinanceEntry


@admin.register(FinanceEntry)
class FinanceEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "entry_type", "amount", "entry_date", "created_by", "admin_actions")
    list_filter = ("entry_type", "entry_date")
    search_fields = ("title", "category")
    date_hierarchy = "entry_date"

    @admin.display(description="Әрекеттер")
    def admin_actions(self, obj):
        change_url = reverse("admin:finance_financeentry_change", args=[obj.pk])
        delete_url = reverse("admin:finance_financeentry_delete", args=[obj.pk])
        return format_html(
            '<span class="nexuserp-actions">'
            '<a href="{}">Өңдеу</a> '
            '<a class="deletelink" href="{}">Өшіру</a>'
            "</span>",
            change_url,
            delete_url,
        )
