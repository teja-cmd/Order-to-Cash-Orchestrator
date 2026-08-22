import pytest
from app.schemas import OrderPayload, LineItem
from app.orchestrator import OrderOrchestrator
from seed_data import seed_db

@pytest.fixture(autouse=True)
def setup_database():
    seed_db()

def test_happy_path():
    orchestrator = OrderOrchestrator()
    payload = OrderPayload(
        customer_id=1, 
        line_items=[
            LineItem(product_id=1, quantity=10),
            LineItem(product_id=2, quantity=5)
        ]
    )
    result = orchestrator.process_order(payload)
    
    assert result.final_status == "COMPLETED"
    assert result.invoice is not None
    assert len(result.handoff_log) == 8 # 4 agents x 2 (request + response)
    
    # Check invoice subtotal
    # Product 1 price = 10.0, Product 2 price = 20.0
    expected_subtotal = (10 * 10.0) + (5 * 20.0)
    assert result.invoice.subtotal == expected_subtotal
    assert result.invoice.tax == expected_subtotal * 0.08
