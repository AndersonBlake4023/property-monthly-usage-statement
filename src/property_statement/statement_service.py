import html
import json
from collections.abc import Mapping
from datetime import date
from typing import Any

from .infrai_client import InfraiClient
from .models import StatementRequest, StatementResult


def should_send_statement(request: StatementRequest, usage: Mapping[str, Any]) -> bool:
    has_property_activity = any(
        (
            request.maintenance_requests,
            request.tenant_documents,
            request.inspection_reminders,
        )
    )
    return bool(usage) or has_property_activity


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_None recorded._"
    heading = "| " + " | ".join(headers) + " |"
    rule = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |" for row in rows]
    return "\n".join([heading, rule, *body])


def render_statement(request: StatementRequest, usage: Mapping[str, Any]) -> str:
    maintenance = [
        [item.reference, item.property_name, item.summary, item.status]
        for item in request.maintenance_requests
    ]
    documents = [
        [item.tenant_name, item.document_name, item.status]
        for item in request.tenant_documents
    ]
    reminders = [
        [item.property_name, item.inspection_type, item.due_on.isoformat()]
        for item in request.inspection_reminders
    ]
    usage_json = json.dumps(usage, indent=2, sort_keys=True, default=str)
    return f"""# Monthly usage statement

**Customer:** {request.customer_name}  
**Statement period:** {request.period_start.isoformat()} to {request.period_end.isoformat()}

## Account usage

```json
{usage_json}
```

## Maintenance requests

{_table(["Reference", "Property", "Summary", "Status"], maintenance)}

## Tenant documents

{_table(["Tenant", "Document", "Status"], documents)}

## Inspection reminders

{_table(["Property", "Inspection", "Due"], reminders)}
"""


def send_monthly_statement(
    request: StatementRequest,
    client: InfraiClient,
) -> StatementResult:
    usage = client.current_usage()
    if not should_send_statement(request, usage):
        return StatementResult(sent=False, reason="No usage or property activity for this period")

    pdf_url = client.generate_pdf(render_statement(request, usage))
    month = request.period_start.strftime("%B %Y")
    safe_customer = html.escape(request.customer_name)
    safe_url = html.escape(pdf_url, quote=True)
    message_id = client.send_email(
        request.customer_email,
        f"{month} property usage statement",
        f"<p>{safe_customer}, your monthly statement is ready.</p>"
        f'<p><a href="{safe_url}">Download the PDF statement</a></p>',
    )
    return StatementResult(sent=True, message_id=message_id, pdf_url=pdf_url)
