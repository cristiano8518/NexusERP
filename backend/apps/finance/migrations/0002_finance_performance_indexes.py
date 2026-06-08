from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="financeentry",
            index=models.Index(fields=["entry_type", "entry_date"], name="finance_type_date_idx"),
        ),
        migrations.AddIndex(
            model_name="financeentry",
            index=models.Index(fields=["category", "entry_date"], name="finance_category_date_idx"),
        ),
    ]
