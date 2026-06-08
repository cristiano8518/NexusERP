from rest_framework import serializers

from .models import FinanceEntry


class FinanceEntrySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = FinanceEntry
        fields = (
            "id",
            "entry_type",
            "title",
            "amount",
            "category",
            "description",
            "entry_date",
            "created_by",
            "created_by_name",
            "created_at",
        )
        read_only_fields = ("id", "created_by", "created_at")

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сома 0-ден үлкен болуы керек.")
        return value
