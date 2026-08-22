from app.schemas import OrderPayload, InventoryResult, InventoryAgentResponse, LineItem
from app.db import get_product
from datetime import datetime

class InventoryAgent:
    name = "InventoryAgent"

    def process(self, order: OrderPayload) -> InventoryAgentResponse:
        fulfillable_items = []
        shortfall_items = []
        
        for item in order.line_items:
            product = get_product(item.product_id)
            if product and product['stock'] >= item.quantity:
                fulfillable_items.append(item)
            elif product and product['stock'] > 0:
                # Can partially fulfill this specific item
                fulfillable_items.append(LineItem(product_id=item.product_id, quantity=product['stock']))
                shortfall_items.append(LineItem(product_id=item.product_id, quantity=item.quantity - product['stock']))
            else:
                # Fully out of stock
                shortfall_items.append(item)

        if not shortfall_items:
            status = "OK"
            suggested_action = "PROCEED"
        elif not fulfillable_items:
            status = "INSUFFICIENT"
            suggested_action = "REJECT"
        else:
            status = "PARTIAL"
            # Judgment call: If more than 50% of distinct items are short, suggest REJECT
            if len(shortfall_items) > len(fulfillable_items):
                suggested_action = "REJECT"
            else:
                suggested_action = "PARTIAL_FULFILLMENT"
                
        return InventoryAgentResponse(
            agent_name=self.name,
            timestamp=datetime.utcnow(),
            status=status,
            payload=InventoryResult(
                status=status,
                fulfillable_items=fulfillable_items,
                shortfall_items=shortfall_items,
                suggested_action=suggested_action
            )
        )

if __name__ == "__main__":
    from app.schemas import LineItem
    agent = InventoryAgent()
    payload = OrderPayload(customer_id=1, line_items=[LineItem(product_id=1, quantity=500)])
    print(agent.process(payload).json(indent=2))
