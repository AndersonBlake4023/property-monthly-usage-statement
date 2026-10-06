import os
from datetime import date

from property_statement.infrai_client import InfraiClient
from property_statement.models import (
    InspectionReminder,
    MaintenanceRequest,
    StatementRequest,
    TenantDocument,
)
from property_statement.statement_service import send_monthly_statement


def main() -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    recipient = os.environ["STATEMENT_RECIPIENT"]
    request = StatementRequest(
        customer_name="Harbor Street Property Management",
        customer_email=recipient,
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        maintenance_requests=[
            MaintenanceRequest(
                reference="MR-1842",
                property_name="Pier Court",
                summary="Replace kitchen tap cartridge",
                status="completed",
            )
        ],
        tenant_documents=[
            TenantDocument(
                tenant_name="A. Rivera",
                document_name="Renewal agreement",
                status="received",
            )
        ],
        inspection_reminders=[
            InspectionReminder(
                property_name="Pier Court",
                due_on=date(2026, 9, 12),
                inspection_type="Annual safety inspection",
            )
        ],
    )
    client = InfraiClient(api_key=api_key)
    try:
        print(send_monthly_statement(request, client).model_dump_json(indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
