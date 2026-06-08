from django.conf import settings
from django.db import models


class FinanceEntry(models.Model):
    class EntryType(models.TextChoices):
        INCOME = "income", "Табыс"
        EXPENSE = "expense", "Шығын"

    entry_type = models.CharField(max_length=10, choices=EntryType.choices, db_index=True)
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    category = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    entry_date = models.DateField(db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="finance_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "finance entries"
        ordering = ["-entry_date", "-created_at"]
        indexes = [
            models.Index(fields=["entry_type", "entry_date"], name="finance_type_date_idx"),
            models.Index(fields=["category", "entry_date"], name="finance_category_date_idx"),
        ]

    def __str__(self):
        return f"{self.get_entry_type_display()}: {self.title}"
