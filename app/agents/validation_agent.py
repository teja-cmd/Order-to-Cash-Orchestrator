from app.schemas import OrderPayload, ValidationResult, ValidationAgentResponse
from app.db import get_customer, get_product
from datetime import datetime

class ValidationAgent:
    name = "ValidationAgent"

    def process(self, order: OrderPayload) -> ValidationAgentResponse:
        errors = []
        
        # Check customer
        customer = get_customer(order.customer_id)
        if not customer:
            errors.append(f"Customer ID {order.customer_id} not found.")

        # Check line items
        if not order.line_items:
            errors.append("Order must contain at least one line item.")
            
        for item in order.line_items:
            if item.quantity <= 0:
                errors.append(f"Product {item.product_id} has invalid quantity: {item.quantity}")
            
            product = get_product(item.product_id)
            if not product:
                errors.append(f"Product ID {item.product_id} not found.")

        is_valid = len(errors) == 0
        
        return ValidationAgentResponse(
            agent_name=self.name,
            timestamp=datetime.utcnow(),
            status="VALID" if is_valid else "INVALID",
            payload=ValidationResult(
                valid=is_valid,
                errors=errors,
                normalized_order=order if is_valid else None
            )
        )

if __name__ == "__main__":
    from app.schemas import LineItem
    agent = ValidationAgent()
    payload = OrderPayload(customer_id=1, line_items=[LineItem(product_id=1, quantity=5)])
    print(agent.process(payload).json(indent=2))
