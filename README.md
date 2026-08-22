# Multi-Agent Order-to-Cash Orchestrator

This project is a sophisticated **multi-agent system** designed to process a sales order end-to-end. By breaking down a traditional monolithic script into discrete, specialized "AI Agents," the system achieves strict separation of concerns, robust exception handling, and a highly observable execution path.

This project was built to satisfy a rigorous Multi-Agent architectural assessment.

---

## 🌟 Key Features

1. **True Multi-Agent Architecture**: Zero heavy frameworks (no LangGraph or CrewAI). The orchestrator and agents are built using plain, highly readable Python classes, making the delegation pattern nakedly visible.
2. **Strict Contracts (Pydantic v2)**: Every handoff between agents is strictly typed. The Orchestrator forces each specialist to return a structured response (`status`, `payload`, `message`), ensuring zero hallucinations during agent handoffs.
3. **Targeted LLM Usage**: Instead of a "single monolithic prompt" that tries to do everything, the LLM (Anthropic Claude 3.5 Sonnet) is aggressively isolated to *only* the `PaymentRiskAgent`. The rest of the pipeline uses deterministic code, proving a true hybrid AI/code design.
4. **Vibrant React Frontend Simulator**: A beautiful, animated UI (built with React + Glassmorphism CSS) that allows reviewers to visually trace the exact execution path and agent handoffs in real-time.
5. **Exception Path Branching**: Intelligently handles complex edge cases like Insufficient Inventory and High-Risk Customers by dynamically altering the orchestrator's state machine.

---

## 🏗️ Architecture & Data Flow

The system employs a **Hub-and-Spoke Orchestrator Pattern**:

```text
       +-------------------+
       |                   | ---> [1. ValidationAgent] (Checks DB for valid IDs)
       |                   |
[POST] | OrderOrchestrator | ---> [2. InventoryAgent] (Checks stock -> Handles Stock Exceptions)
       |                   |
       |                   | ---> [3. InvoicingAgent] (Performs Math & Subtotals)
       |                   |
       |                   | ---> [4. PaymentRiskAgent] (LLM checks payment history -> Handles Risk)
       +-------------------+
```

### The Specialist Agents
1. **OrderOrchestrator**: The central router. It contains *zero* domain logic. It simply maintains the state machine, catches exceptions, and sequentially passes the JSON payload to the appropriate specialist.
2. **ValidationAgent**: The first line of defense. Checks if the incoming Customer ID and Product IDs actually exist in the SQLite database, ensuring downstream agents don't crash on bad data.
3. **InventoryAgent**: Queries the database to check stock levels against the requested quantities. 
4. **InvoicingAgent**: Takes the fulfillable items and calculates the math (subtotals, 8% tax rate, and final totals) to generate a digital invoice.
5. **PaymentRiskAgent**: The AI Financial Analyst. It takes the customer's historical payment data (from SQLite) and the final invoice amount, formats a prompt, and asks **Claude 3.5 Sonnet** to determine if the user is a `LOW`, `MEDIUM`, or `HIGH` payment risk.

---

## ⚠️ Exception Handling Paths

The assessment required handling at least one failure/exception path. This project handles **two**:

1. **Insufficient Inventory**:
   - If a customer requests 100 units of a product but only 50 are in stock, the `InventoryAgent` catches this.
   - It performs mathematical logic to decide whether to *completely reject* the order or propose a **Partial Fulfillment**. 
   - If partially fulfilled, the Orchestrator intelligently routes the modified quantities to the `InvoicingAgent`, and the final status is tagged as `PARTIAL_FULFILLMENT`.

2. **High Payment Risk**:
   - If the `PaymentRiskAgent` (powered by the LLM) determines that a customer has a terrible payment history (e.g., constantly 60+ days late), it flags the order.
   - The Orchestrator intercepts this flag and overrides the final pipeline status to `FLAGGED_FOR_REVIEW`, halting the automated cash collection.

---

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.11)
- **Data Validation**: Pydantic v2
- **Database**: SQLite (via SQLAlchemy) for mock inventory, customers, and payment histories.
- **Frontend**: React 18 (Standalone) with custom vanilla CSS (Glassmorphism & CSS Animations). Served natively via FastAPI `StaticFiles`.
- **AI / LLM**: Anthropic API (`claude-3-5-sonnet-20241022`).
- **Testing**: Pytest.

---

## 🚀 Setup & Running

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Seed the Database**:
   Populates the SQLite database with the mock data needed for testing.
   ```bash
   python seed_data.py
   ```

3. **Set your Anthropic API Key**:
   ```bash
   # Windows (PowerShell)
   $env:ANTHROPIC_API_KEY="your-api-key-here"
   
   # Linux/macOS
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

4. **Run the Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **View the UI Simulator**:
   Navigate to **http://localhost:8000** in your web browser. 
   You will see the React interface where you can select predefined scenarios (Happy Path, Insufficient Inventory, etc.), submit them, and watch the Agent Handoff Log populate in real-time.

---

## 🧪 Running Tests

A test suite is included to verify the deterministic logic of the orchestrator, specifically covering the Happy Path and the Insufficient Inventory exception path.

Execute the pytest suite:
```bash
python -m pytest tests/
```

---

## 📝 Design Decisions & Constraints Answered

- **Why no heavy frameworks (LangGraph/AutoGen)?** The prompt requested a *clear orchestrator-to-specialist delegation pattern*. Heavy frameworks hide the delegation behind abstractions. By writing a custom `OrderOrchestrator` class, the handoffs are explicitly readable in standard Python.
- **Why 4 Specialists instead of 2?** The problem domain neatly divides into four distinct bounded contexts (Validation, Inventory, Math, and Risk). Combining them would violate the single-responsibility principle of agent design.
- **Why use React Standalone?** To provide a vibrant, interactive UI without forcing the reviewer to install Node.js/npm. The React app is compiled in the browser via Babel and served directly by FastAPI for maximum convenience.
