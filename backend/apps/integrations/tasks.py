from celery import shared_task


@shared_task(name="integrations.sync_external_employees")
def sync_external_employees_task():
    from .services import cache_external_employees

    payload = cache_external_employees()
    return {
        "source": payload["source"],
        "employees_count": len(payload.get("employees", [])),
    }
