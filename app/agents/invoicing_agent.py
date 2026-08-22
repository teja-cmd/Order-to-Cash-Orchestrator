from app.schemas import LineItem, InvoiceLineItem, Invoice, InvoicingAgentResponse
from app.db import get_product
from datetime import datetime
from typing import List
import uuid

class InvoicingAgent:
    name = "InvoicingAgent"

    def process(self, fulfillable_items: List[LineItem], is_partial: bool) -> InvoicingAgentResponse:
        invoice_lines = []
        subtotal = 0.0
        
        for item in fulfillable_items:
            product = get_product(item.product_id)
            if product:
                line_total = product['price'] * item.quantity
                subtotal += line_total
                invoice_lines.append(InvoiceLineItem(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=product['price'],
                    line_total=line_total
                ))
                
        tax_rate = 0.08
        tax = subtotal * tax_rate
        total = subtotal + tax
        
        fulfillment_note = "Partial Invoice - Some items backordered or rejected." if is_partial else "Full Invoice"
        
        invoice = Invoice(
            invoice_id=str(uuid.uuid4()),
            line_items=invoice_lines,
            subtotal=subtotal,
            tax=tax,
            total=total,
            fulfillment_note=fulfillment_note
        )
        
        return InvoicingAgentResponse(
            agent_name=self.name,
            timestamp=datetime.utcnow(),
            status="INVOICED",
            payload=invoice
        )

if __name__ == "__main__":
    agent = InvoicingAgent()
    print(agent.process([LineItem(product_id=1, quantity=5)], False).json(indent=2))
