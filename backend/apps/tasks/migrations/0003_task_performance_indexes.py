from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0002_task_workflow_history"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="task",
            index=models.Index(fields=["status", "priority"], name="task_status_priority_idx"),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(fields=["assignee", "status"], name="task_assignee_status_idx"),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(fields=["deadline", "status"], name="task_deadline_status_idx"),
        ),
    ]
