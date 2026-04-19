import streamlit as st
import grpc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import sys
import os

# Add src to path to import generated files
sys.path.append(os.path.join(os.getcwd(), "src"))
from limbic.generated import limbic_pb2, limbic_pb2_grpc

st.set_page_config(page_title="Limbic System Dashboard", layout="wide")

st.title("🧠 Autonomous Agent Limbic System & PFC Dashboard")

# Connection sidebar
st.sidebar.header("Connection Settings")
grpc_host = st.sidebar.text_input("gRPC Host", "localhost")
grpc_port = st.sidebar.text_input("gRPC Port", "50051")

channel = grpc.insecure_channel(f"{grpc_host}:{grpc_port}")
stub = limbic_pb2_grpc.LimbicServiceStub(channel)

# Main layout
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Limbic State")
    state_placeholder = st.empty()
    
    st.header("Emotional Valence & Arousal")
    chart_placeholder = st.empty()

with col2:
    st.header("Executive Layer (PFC)")
    plans_placeholder = st.empty()
    
    st.header("Active Drives")
    drives_placeholder = st.empty()

# Persistent state for charts
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["timestamp", "valence", "arousal"])

def update_dashboard():
    try:
        # Get Limbic State
        state = stub.GetLimbicState(limbic_pb2.Empty())
        
        # Update State Text
        state_placeholder.json({
            "arousal": state.arousal,
            "valence": state.valence,
            "dominant_engine": state.dominant_engine,
            "timestamp": state.timestamp
        })
        
        # Update History
        new_row = pd.DataFrame([{
            "timestamp": time.time(),
            "valence": state.valence,
            "arousal": state.arousal
        }])
        st.session_state.history = pd.concat([st.session_state.history, new_row]).tail(50)
        
        # Update Chart
        fig = px.scatter(st.session_state.history, x="valence", y="arousal", 
                         range_x=[-1, 1], range_y=[0, 1],
                         title="Affective Space (Valence/Arousal)")
        fig.add_shape(type="line", x0=-1, y0=0.5, x1=1, y1=0.5, line=dict(color="gray", dash="dash"))
        fig.add_shape(type="line", x0=0, y0=0, x1=0, y1=1, line=dict(color="gray", dash="dash"))
        chart_placeholder.plotly_chart(fig, use_container_with_width=True)
        
        # Update Drives
        drives_df = pd.DataFrame(list(state.drives.items()), columns=["Drive", "Level"])
        if not drives_df.empty:
            drives_placeholder.bar_chart(drives_df.set_index("Drive"))
        else:
            drives_placeholder.write("No active drives")
            
        # Get Plans
        plans_resp = stub.GetPlans(limbic_pb2.Empty())
        plans_data = []
        for p in plans_resp.plans:
            plans_data.append({
                "Action": p.action,
                "Confidence": p.confidence,
                "Utility": p.utility,
                "Approved": p.approved,
                "Status": p.status
            })
        
        if plans_data:
            plans_placeholder.table(pd.DataFrame(plans_data))
        else:
            plans_placeholder.write("No active plans in PFC")

    except Exception as e:
        st.error(f"Error connecting to Limbic Daemon: {e}")

# Stimulus Injection
st.sidebar.header("Inject Stimulus")
stim_content = st.sidebar.text_area("Content")
stim_source = st.sidebar.text_input("Source", "User")
if st.sidebar.button("Inject"):
    try:
        # Simple random embedding for demonstration
        import numpy as np
        embedding = np.random.rand(128).tolist()
        stub.InjectStimulus(limbic_pb2.StimulusRequest(
            source=stim_source,
            content=stim_content,
            embedding=embedding
        ))
        st.sidebar.success("Stimulus injected!")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# Auto-refresh loop
while True:
    update_dashboard()
    time.sleep(2)
    st.rerun()
