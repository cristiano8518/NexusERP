from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("warehouse", "0002_stockmovement_finance"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["category", "is_active"], name="product_category_active_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["quantity", "min_stock_level"], name="product_stock_level_idx"),
        ),
        migrations.AddIndex(
            model_name="stockmovement",
            index=models.Index(fields=["product", "created_at"], name="stock_product_created_idx"),
        ),
        migrations.AddIndex(
            model_name="stockmovement",
            index=models.Index(fields=["movement_type", "created_at"], name="stock_type_created_idx"),
        ),
    ]
