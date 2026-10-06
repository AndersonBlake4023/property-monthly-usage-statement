from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class MaintenanceRequest(BaseModel):
    reference: str
    property_name: str
    summary: str
    status: Literal["open", "scheduled", "completed"]


class TenantDocument(BaseModel):
    tenant_name: str
    document_name: str
    status: Literal["received", "missing", "expiring"]


class InspectionReminder(BaseModel):
    property_name: str
    due_on: date
    inspection_type: str


class StatementRequest(BaseModel):
    customer_name: str
    customer_email: str
    period_start: date
    period_end: date
    maintenance_requests: list[MaintenanceRequest] = Field(default_factory=list)
    tenant_documents: list[TenantDocument] = Field(default_factory=list)
    inspection_reminders: list[InspectionReminder] = Field(default_factory=list)

    @field_validator("customer_email")
    @classmethod
    def email_has_address_shape(cls, value: str) -> str:
        local, separator, domain = value.partition("@")
        if not local or not separator or "." not in domain:
            raise ValueError("customer_email must be an email address")
        return value

    @model_validator(mode="after")
    def dates_are_ordered(self) -> "StatementRequest":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class StatementResult(BaseModel):
    sent: bool
    message_id: str | None = None
    pdf_url: str | None = None
    reason: str | None = None
