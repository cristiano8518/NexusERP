from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Category, Product, StockMovement


def action_links(obj, app_model: str):
    change_url = reverse(f"admin:{app_model}_change", args=[obj.pk])
    delete_url = reverse(f"admin:{app_model}_delete", args=[obj.pk])
    return format_html(
        '<span class="nexuserp-actions">'
        '<a href="{}">Өңдеу</a> '
        '<a class="deletelink" href="{}">Өшіру</a>'
        "</span>",
        change_url,
        delete_url,
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "admin_actions")

    @admin.display(description="Әрекеттер")
    def admin_actions(self, obj):
        return action_links(obj, "warehouse_category")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "quantity", "is_active", "admin_actions")
    list_filter = ("category", "is_active")
    search_fields = ("sku", "name")

    @admin.display(description="Әрекеттер")
    def admin_actions(self, obj):
        return action_links(obj, "warehouse_product")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "movement_type",
        "quantity",
        "unit_price",
        "total_amount",
        "finance_entry",
        "created_at",
        "admin_actions",
    )
    list_filter = ("movement_type",)

    @admin.display(description="Әрекеттер")
    def admin_actions(self, obj):
        return action_links(obj, "warehouse_stockmovement")
