
import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import grpc
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from limbic.generated import limbic_pb2, limbic_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WSProxy")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GRPC_HOST = os.getenv("GRPC_HOST", "localhost")
GRPC_PORT = os.getenv("GRPC_PORT", "50051")

@app.websocket("/ws/limbic")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    channel = grpc.aio.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
    stub = limbic_pb2_grpc.LimbicServiceStub(channel)
    
    try:
        # Subscribe to the state stream from gRPC
        async for state in stub.StreamState(limbic_pb2.Empty()):
            # Convert gRPC message to dict
            # We can't use MessageToDict because of some gRPC specific types in the proto
            # So we manually construct a simple dict for the frontend
            
            recent_thoughts = []
            for t in state.recent_thoughts:
                recent_thoughts.append({
                    "thought_id": t.thought_id,
                    "content": t.content,
                    "signer_id": t.signer_id
                })

            data = {
                "arousal": state.arousal,
                "valence": state.valence,
                "dominant_engine": state.dominant_engine,
                "phi": state.phi,
                "ego_coherence": state.ego_coherence,
                "meaning": state.meaning,
                "dread": state.dread,
                "timestamp": state.timestamp,
                "hormones": dict(state.hormones),
                "recent_thoughts": recent_thoughts
            }
            await websocket.send_text(json.dumps(data))
    except Exception as e:
        logger.error(f"Error in gRPC stream: {e}")
    finally:
        await channel.close()
        logger.info("WebSocket connection closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
