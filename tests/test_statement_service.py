from datetime import date

from property_statement.models import MaintenanceRequest, StatementRequest
from property_statement.statement_service import send_monthly_statement


class RecordingClient:
    def __init__(self, usage: dict[str, object]) -> None:
        self.usage = usage
        self.pdf_markdown: str | None = None
        self.email_html: str | None = None

    def current_usage(self) -> dict[str, object]:
        return self.usage

    def generate_pdf(self, markdown: str) -> str:
        self.pdf_markdown = markdown
        return "https://documents.example/statement.pdf"

    def send_email(self, to: str, subject: str, html: str) -> str:
        self.email_html = html
        return "message-42"


def request_with_maintenance() -> StatementRequest:
    return StatementRequest(
        customer_name="Harbor Street",
        customer_email="records@example.com",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        maintenance_requests=[
            MaintenanceRequest(
                reference="MR-1842",
                property_name="Pier Court",
                summary="Replace tap cartridge",
                status="completed",
            )
        ],
    )


def test_activity_is_rendered_and_pdf_url_is_handed_to_email() -> None:
    client = RecordingClient({"requests": 17})

    result = send_monthly_statement(request_with_maintenance(), client)  # type: ignore[arg-type]

    assert result.sent is True
    assert result.message_id == "message-42"
    assert "MR-1842" in (client.pdf_markdown or "")
    assert "https://documents.example/statement.pdf" in (client.email_html or "")


def test_empty_month_is_not_sent() -> None:
    request = request_with_maintenance().model_copy(update={"maintenance_requests": []})
    client = RecordingClient({})

    result = send_monthly_statement(request, client)  # type: ignore[arg-type]

    assert result.sent is False
    assert client.pdf_markdown is None
