import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0001_initial"),
        ("warehouse", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="stockmovement",
            name="auto_create_finance",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="stockmovement",
            name="finance_entry",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="stock_movement",
                to="finance.financeentry",
            ),
        ),
        migrations.AddField(
            model_name="stockmovement",
            name="total_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name="stockmovement",
            name="unit_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]
