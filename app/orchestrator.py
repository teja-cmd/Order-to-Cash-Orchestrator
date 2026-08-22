from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from app.schemas import (
    OrderPayload, HandoffLogEntry, ValidationAgentResponse, 
    InventoryAgentResponse, InvoicingAgentResponse, PaymentRiskAgentResponse
)
from app.agents.validation_agent import ValidationAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.invoicing_agent import InvoicingAgent
from app.agents.payment_risk_agent import PaymentRiskAgent

class OrchestratorResponse(BaseModel):
    final_status: str
    message: str
    handoff_log: List[HandoffLogEntry]
    invoice: Optional[Any] = None

class OrderOrchestrator:
    def __init__(self):
        self.handoff_log: List[HandoffLogEntry] = []
        self.validation_agent = ValidationAgent()
        self.inventory_agent = InventoryAgent()
        self.invoicing_agent = InvoicingAgent()
        self.payment_risk_agent = PaymentRiskAgent()
        
    def _log(self, from_agent: str, to_agent: str, direction: str, summary: str):
        entry = HandoffLogEntry(
            step=len(self.handoff_log) + 1,
            from_agent=from_agent,
            to_agent=to_agent,
            direction=direction,
            summary=summary,
            timestamp=datetime.utcnow()
        )
        self.handoff_log.append(entry)
        print(f"[{entry.direction}] {entry.from_agent} -> {entry.to_agent} | {entry.summary}")

    def process_order(self, order: OrderPayload) -> OrchestratorResponse:
        self.handoff_log = []
        status = "RECEIVED"
        
        # 1. Validation
        self._log("Orchestrator", self.validation_agent.name, "REQUEST", "Validating order payload")
        val_resp: ValidationAgentResponse = self.validation_agent.process(order)
        self._log(self.validation_agent.name, "Orchestrator", "RESPONSE", val_resp.to_log_line())
        
        if val_resp.status == "INVALID":
            return OrchestratorResponse(
                final_status="REJECTED",
                message=f"Order validation failed: {', '.join(val_resp.payload.errors)}",
                handoff_log=self.handoff_log
            )
            
        status = "VALIDATED"
        normalized_order = val_resp.payload.normalized_order
        
        # 2. Inventory
        self._log("Orchestrator", self.inventory_agent.name, "REQUEST", "Checking inventory levels")
        inv_resp: InventoryAgentResponse = self.inventory_agent.process(normalized_order)
        self._log(self.inventory_agent.name, "Orchestrator", "RESPONSE", inv_resp.to_log_line())
        
        if inv_resp.payload.suggested_action == "REJECT":
            return OrchestratorResponse(
                final_status="REJECTED",
                message="Order rejected due to insufficient inventory.",
                handoff_log=self.handoff_log
            )
            
        is_partial = inv_resp.payload.suggested_action == "PARTIAL_FULFILLMENT"
        if is_partial:
            status = "PARTIAL_FULFILLMENT"
        else:
            status = "INVENTORY_CONFIRMED"
            
        # 3. Invoicing
        self._log("Orchestrator", self.invoicing_agent.name, "REQUEST", "Generating invoice")
        inv_payload = inv_resp.payload.fulfillable_items
        invoice_resp: InvoicingAgentResponse = self.invoicing_agent.process(inv_payload, is_partial)
        self._log(self.invoicing_agent.name, "Orchestrator", "RESPONSE", invoice_resp.to_log_line())
        
        status = "INVOICED"
        invoice_data = invoice_resp.payload
        
        # 4. Payment Risk
        self._log("Orchestrator", self.payment_risk_agent.name, "REQUEST", f"Assessing risk for customer {order.customer_id}")
        risk_resp: PaymentRiskAgentResponse = self.payment_risk_agent.process(order.customer_id, invoice_data.total)
        self._log(self.payment_risk_agent.name, "Orchestrator", "RESPONSE", risk_resp.to_log_line())
        
        if risk_resp.payload.risk_level == "HIGH":
            status = "FLAGGED_FOR_REVIEW"
        elif is_partial:
            status = "PARTIAL_FULFILLMENT"
        else:
            status = "COMPLETED"
            
        return OrchestratorResponse(
            final_status=status,
            message="Order processing completed.",
            handoff_log=self.handoff_log,
            invoice=invoice_data
        )

if __name__ == "__main__":
    from app.schemas import LineItem
    orch = OrderOrchestrator()
    payload = OrderPayload(customer_id=1, line_items=[LineItem(product_id=1, quantity=1)])
    result = orch.process_order(payload)
    print(f"Final Status: {result.final_status}")
