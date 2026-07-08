from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_user_groups"),
        ("accounts", "0002_auditlog"),
    ]

    operations = []
