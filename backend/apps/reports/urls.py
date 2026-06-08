from django.urls import path

from .views import (
    AsyncReportView,
    EmployeeReportCsvView,
    FinanceReportCsvView,
    ReportSummaryView,
    TaskReportCsvView,
    WarehouseReportCsvView,
)

urlpatterns = [
    path("summary/", ReportSummaryView.as_view(), name="reports-summary"),
    path("async/", AsyncReportView.as_view(), name="reports-async"),
    path("tasks.csv", TaskReportCsvView.as_view(), name="reports-tasks-csv"),
    path("finance.csv", FinanceReportCsvView.as_view(), name="reports-finance-csv"),
    path("warehouse.csv", WarehouseReportCsvView.as_view(), name="reports-warehouse-csv"),
    path("employees.csv", EmployeeReportCsvView.as_view(), name="reports-employees-csv"),
]
