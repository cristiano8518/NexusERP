from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="notification_type",
            field=models.CharField(
                choices=[
                    ("task_assigned", "Тапсырма берілді"),
                    ("task_started", "Тапсырма басталды"),
                    ("task_submitted", "Тексеруге жіберілді"),
                    ("task_approved", "Тапсырма бекітілді"),
                    ("task_rejected", "Тапсырма қайтарылды"),
                    ("task_comment", "Тапсырма пікірі"),
                    ("deadline", "Мерзім"),
                    ("low_stock", "Төмен қор"),
                    ("system", "Жүйе"),
                ],
                db_index=True,
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="priority",
            field=models.CharField(
                choices=[
                    ("low", "Төмен"),
                    ("normal", "Қалыпты"),
                    ("high", "Жоғары"),
                ],
                default="normal",
                max_length=10,
            ),
        ),
    ]
