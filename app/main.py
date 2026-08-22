from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.schemas import OrderPayload
from app.orchestrator import OrderOrchestrator, OrchestratorResponse

app = FastAPI(title="Order-to-Cash Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/orders/process", response_model=OrchestratorResponse)
def process_order(order: OrderPayload):
    try:
        orchestrator = OrderOrchestrator()
        result = orchestrator.process_order(order)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files (React frontend) at the root
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
