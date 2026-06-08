from rest_framework import serializers

from .models import Category, Product, StockMovement


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "description")


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    inventory_value = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "name",
            "category",
            "category_name",
            "unit",
            "quantity",
            "min_stock_level",
            "price",
            "inventory_value",
            "is_low_stock",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "created_at", "quantity")

    def get_inventory_value(self, obj):
        return obj.quantity * obj.price


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    finance_entry_id = serializers.IntegerField(source="finance_entry.id", read_only=True)

    class Meta:
        model = StockMovement
        fields = (
            "id",
            "product",
            "product_name",
            "movement_type",
            "quantity",
            "unit_price",
            "total_amount",
            "note",
            "auto_create_finance",
            "finance_entry_id",
            "created_by",
            "created_at",
        )
        read_only_fields = ("id", "total_amount", "finance_entry_id", "created_by", "created_at")

    def validate(self, attrs):
        product = attrs.get("product")
        movement_type = attrs.get("movement_type")
        quantity = attrs.get("quantity")
        if movement_type == StockMovement.MovementType.OUT and product and quantity:
            if quantity > product.quantity:
                raise serializers.ValidationError(
                    {"quantity": "Қоймада жеткілікті қалдық жоқ."}
                )
        return attrs
