from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Literal, Optional, Any

class LineItem(BaseModel):
    product_id: int
    quantity: int

class OrderPayload(BaseModel):
    customer_id: int
    line_items: List[LineItem]

class BaseAgentResponse(BaseModel):
    agent_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str
    payload: Any

    def to_log_line(self) -> str:
        return f"[{self.timestamp.isoformat()}] {self.agent_name} -> {self.status}"

# Validation Agent
class ValidationResult(BaseModel):
    valid: bool
    errors: List[str]
    normalized_order: Optional[OrderPayload] = None

class ValidationAgentResponse(BaseAgentResponse):
    status: Literal["VALID", "INVALID"]
    payload: ValidationResult

    def to_log_line(self) -> str:
        return f"[{self.timestamp.isoformat()}] {self.agent_name} -> {self.status}: valid={self.payload.valid}"

# Inventory Agent
class InventoryResult(BaseModel):
    status: Literal["OK", "PARTIAL", "INSUFFICIENT"]
    fulfillable_items: List[LineItem]
    shortfall_items: List[LineItem]
    suggested_action: Literal["PROCEED", "PARTIAL_FULFILLMENT", "REJECT"]

class InventoryAgentResponse(BaseAgentResponse):
    status: Literal["OK", "PARTIAL", "INSUFFICIENT"]
    payload: InventoryResult

    def to_log_line(self) -> str:
        return f"[{self.timestamp.isoformat()}] {self.agent_name} -> {self.status}: suggested_action={self.payload.suggested_action}"

# Invoicing Agent
class InvoiceLineItem(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    line_total: float

class Invoice(BaseModel):
    invoice_id: str
    line_items: List[InvoiceLineItem]
    subtotal: float
    tax: float
    total: float
    fulfillment_note: str

class InvoicingAgentResponse(BaseAgentResponse):
    status: Literal["INVOICED"]
    payload: Invoice

    def to_log_line(self) -> str:
        return f"[{self.timestamp.isoformat()}] {self.agent_name} -> {self.status}: total={self.payload.total}"

# Payment Risk Agent
class PaymentRiskResult(BaseModel):
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    rationale: str

class PaymentRiskAgentResponse(BaseAgentResponse):
    status: Literal["ASSESSED"]
    payload: PaymentRiskResult

    def to_log_line(self) -> str:
        return f"[{self.timestamp.isoformat()}] {self.agent_name} -> {self.status}: risk_level={self.payload.risk_level}"

# Handoff Log Entry
class HandoffLogEntry(BaseModel):
    step: int
    from_agent: str
    to_agent: str
    direction: Literal["REQUEST", "RESPONSE"]
    summary: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
