import streamlit as st
import requests
import json
import os
import sys

# Add parent directory to path so imports work correctly in Streamlit Cloud
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db import DB_PATH
if not os.path.exists(DB_PATH):
    import seed_data
    seed_data.seed_db()

from app.orchestrator import OrderOrchestrator
from app.schemas import OrderPayload

st.set_page_config(page_title="Order-to-Cash Orchestrator", layout="wide")

st.title("Multi-Agent Order-to-Cash Orchestrator")
st.markdown("Submit an order to the multi-agent system and watch the real-time handoff log.")

# Load site CSS from the repo `static/styles.css` so Streamlit shows the same styling
def _load_css_with_fallback(local_path, raw_url=None):
    css = None
    source = None
    # Try local file first
    try:
        with open(local_path, 'r', encoding='utf-8') as f:
            css = f.read()
            source = 'local'
    except Exception:
        css = None

    # If local failed and a raw URL is provided, try fetching it
    if not css and raw_url:
        try:
            resp = requests.get(raw_url, timeout=5)
            if resp.status_code == 200:
                css = resp.text
                source = 'raw'
        except Exception:
            css = None

    # Inject CSS if we have it
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    return source

css_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'styles.css')
raw_css_url = "https://raw.githubusercontent.com/teja-cmd/Order-to-Cash-Orchestrator/main/static/styles.css"
css_source = _load_css_with_fallback(css_file, raw_css_url)

# Small on-screen debug caption so we can confirm where CSS loaded from
try:
    src_label = css_source if css_source else 'none'
    st.caption(f"CSS source: {src_label}")
except Exception:
    pass

# Load mock data
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
mock_file = os.path.join(data_dir, 'mock_orders.json')

scenarios = {}
if os.path.exists(mock_file):
    with open(mock_file, 'r') as f:
        scenarios = json.load(f)

scenario_names = list(scenarios.keys()) if scenarios else ["No mock data found"]
selected_scenario = st.selectbox("Select a test scenario:", scenario_names)

if selected_scenario in scenarios:
    payload_str = json.dumps(scenarios[selected_scenario], indent=2)
else:
    payload_str = "{}"
    
payload = st.text_area("Order Payload (JSON):", value=payload_str, height=250)

if st.button("Process Order"):
    try:
        order_data = json.loads(payload)
        order_payload = OrderPayload(**order_data)
        with st.spinner("Processing..."):
            orchestrator = OrderOrchestrator()
            result = orchestrator.process_order(order_payload)
            
            st.subheader("Processing Result")
            status_color = "green" if result.final_status == "COMPLETED" else "orange" if "PARTIAL" in result.final_status else "red"
            st.markdown(f"**Final Status**: :{status_color}[{result.final_status}]")
            st.write(result.message)
            
            if result.invoice:
                with st.expander("View Invoice Details"):
                    st.json(result.invoice.model_dump() if hasattr(result.invoice, 'model_dump') else result.invoice.dict())
            
            st.subheader("Agent Handoff Log")
            for entry in result.handoff_log:
                direction = "➡️" if entry.direction == "REQUEST" else "⬅️"
                st.markdown(f"""
                **Step {entry.step}** ({entry.timestamp}):  
                {entry.from_agent} {direction} {entry.to_agent}  
                `{entry.summary}`
                """)
                st.divider()
    except Exception as e:
        st.error(f"Failed to process: {str(e)}")
