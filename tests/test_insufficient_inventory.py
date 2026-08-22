import pytest
from app.schemas import OrderPayload, LineItem
from app.orchestrator import OrderOrchestrator
from seed_data import seed_db

@pytest.fixture(autouse=True)
def setup_database():
    seed_db()

def test_partial_fulfillment():
    orchestrator = OrderOrchestrator()
    payload = OrderPayload(
        customer_id=1, 
        line_items=[
            LineItem(product_id=1, quantity=10), # OK (stock 100)
            LineItem(product_id=3, quantity=5)   # INSUFFICIENT (stock 0)
        ]
    )
    result = orchestrator.process_order(payload)
    
    assert result.final_status == "PARTIAL_FULFILLMENT"
    assert result.invoice is not None
    # Only Product 1 should be invoiced
    assert len(result.invoice.line_items) == 1
    assert result.invoice.line_items[0].product_id == 1

def test_rejected_due_to_inventory():
    orchestrator = OrderOrchestrator()
    payload = OrderPayload(
        customer_id=1, 
        line_items=[
            LineItem(product_id=3, quantity=5),   # INSUFFICIENT (stock 0)
            LineItem(product_id=4, quantity=10)   # PARTIAL (stock 3)
        ]
    )
    result = orchestrator.process_order(payload)
    
    # 2 shortfalls, 1 fulfillable -> rejects
    assert result.final_status == "REJECTED"
    assert "insufficient inventory" in result.message
    assert result.invoice is None
