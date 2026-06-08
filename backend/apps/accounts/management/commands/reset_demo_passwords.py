from django.core.management.base import BaseCommand

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Reset demo user passwords (admin123, manager123, employee123)"

    def handle(self, *args, **options):
        accounts = [
            ("admin", "admin123"),
            ("manager", "manager123"),
            ("employee", "employee123"),
        ]
        for username, password in accounts:
            try:
                user = User.objects.get(username=username)
                user.set_password(password)
                user.is_active = True
                if username == "admin":
                    user.is_staff = True
                    user.is_superuser = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f"OK: {username} -> {password}"))
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"SKIP: {username} not found — run seed_demo first"))

        self.stdout.write(self.style.SUCCESS("Done. Try login again at http://localhost:3000/login"))
