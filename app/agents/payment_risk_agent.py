import os
import json
from anthropic import Anthropic
from app.schemas import PaymentRiskResult, PaymentRiskAgentResponse
from app.db import get_customer_payment_history
from datetime import datetime

class PaymentRiskAgent:
    name = "PaymentRiskAgent"

    def __init__(self):
        # We assume ANTHROPIC_API_KEY is in the environment
        api_key = os.environ.get("ANTHROPIC_API_KEY", "dummy_key_for_testing")
        self.client = Anthropic(api_key=api_key)

    def process(self, customer_id: int, invoice_total: float) -> PaymentRiskAgentResponse:
        history = get_customer_payment_history(customer_id)
        
        # Prepare context for LLM
        prompt = f"""
        You are a payment risk analyst. Assess the payment risk for this customer based on their history.
        Invoice Total: ${invoice_total}
        Payment History: {json.dumps(history, indent=2)}
        
        Respond ONLY with a valid JSON object matching this schema, no markdown, no other text:
        {{
            "risk_level": "LOW" | "MEDIUM" | "HIGH",
            "rationale": "A brief explanation"
        }}
        """
        
        risk_level = "MEDIUM"
        rationale = "Fallback rationale"
        
        try:
            # We use Claude 3.5 Sonnet
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                temperature=0.0,
                system="You are a strict JSON-only API that outputs risk assessments.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse defensively
            text = response.content[0].text.strip()
            # Strip code fences if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            data = json.loads(text.strip())
            risk_level = data.get("risk_level", "MEDIUM")
            if risk_level not in ["LOW", "MEDIUM", "HIGH"]:
                risk_level = "MEDIUM"
            rationale = data.get("rationale", "Parsed from LLM")
            
        except Exception as e:
            # Deterministic fallback heuristic
            if not history:
                risk_level = "MEDIUM"
                rationale = "No payment history available (fallback heuristic)."
            else:
                late_payments = sum(1 for p in history if p.get('status') == 'LATE')
                if late_payments > 0:
                    risk_level = "HIGH"
                    rationale = f"Customer has {late_payments} late payments (fallback heuristic)."
                else:
                    risk_level = "LOW"
                    rationale = "Customer has a clean payment history (fallback heuristic)."

        result = PaymentRiskResult(
            risk_level=risk_level,
            rationale=rationale
        )
        
        return PaymentRiskAgentResponse(
            agent_name=self.name,
            timestamp=datetime.utcnow(),
            status="ASSESSED",
            payload=result
        )

if __name__ == "__main__":
    agent = PaymentRiskAgent()
    print(agent.process(1, 500.0).json(indent=2))
