import asyncio
import logging
import time
from typing import Dict, Any, Optional
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class GlobalWorkspace:
    """
    Global Workspace Theory (GWT) implementation.
    Acts as a competitive bottleneck for signals from across the system.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.contents: Dict[str, Dict[str, Any]] = {}
        self.conscious_content: Optional[Dict[str, Any]] = None
        self.last_broadcast_time = 0
        self.hysteresis_threshold = 0.2 # Minimum salience lead to switch focus
        
        # Topic weights for salience calculation
        self.weights = {
            "STIMULUS": 0.5,
            "EMOTION_EVOKED": 0.7,
            "CONFLICT_DETECTED": 0.9,
            "UTILITY_ASSIGNED": 0.4,
            "SOCIAL_SIGNAL": 0.6
        }
        
        self.bus.subscribe("STIMULUS", lambda data: self.on_signal("STIMULUS", data))
        self.bus.subscribe("EMOTION_EVOKED", lambda data: self.on_signal("EMOTION_EVOKED", data))
        self.bus.subscribe("CONFLICT_DETECTED", lambda data: self.on_signal("CONFLICT_DETECTED", data))
        self.bus.subscribe("UTILITY_ASSIGNED", lambda data: self.on_signal("UTILITY_ASSIGNED", data))
        self.bus.subscribe("SOCIAL_SIGNAL", lambda data: self.on_signal("SOCIAL_SIGNAL", data))

    def on_signal(self, topic: str, data: Any):
        # Calculate salience
        base_weight = self.weights.get(topic, 0.1)
        
        # Extract intrinsic importance if available
        intrinsic = 0.5
        if hasattr(data, "metadata") and isinstance(data.metadata, dict) and "salience" in data.metadata:
            intrinsic = data.metadata["salience"]
        elif isinstance(data, dict):
            intrinsic = data.get("level", data.get("severity", data.get("arousal", 0.5)))
        elif hasattr(data, "metadata"): # For protobuf objects
             metadata = getattr(data, 'metadata', {})
             if "salience" in metadata:
                 intrinsic = metadata["salience"]
        
        salience = base_weight * intrinsic
        
        # Store in competitive buffer
        content_id = f"{topic}_{time.time()}"
        if topic == "CONFLICT_DETECTED" and isinstance(data, dict):
            content_id = f"CONFLICT_{data.get('id', 'unknown')}"
        
        self.contents[content_id] = {
            "topic": topic,
            "data": data,
            "salience": salience,
            "timestamp": time.time()
        }

    async def run(self):
        logger.info("Global Workspace starting...")
        while True:
            await self.update_workspace()
            await asyncio.sleep(0.5)

    async def update_workspace(self):
        now = time.time()
        # Decay salience and remove old contents
        to_delete = []
        for cid, content in self.contents.items():
            age = now - content["timestamp"]
            content["salience"] *= 0.8 # Decay
            if content["salience"] < 0.1 or age > 10:
                to_delete.append(cid)
        
        for cid in to_delete:
            del self.contents[cid]
            
        if not self.contents:
            return

        # Competition
        winner_id = max(self.contents, key=lambda k: self.contents[k]["salience"])
        winner = self.contents[winner_id]
        
        # Hysteresis
        current_salience = self.conscious_content["salience"] if self.conscious_content else 0
        if winner["salience"] > current_salience + self.hysteresis_threshold or (now - self.last_broadcast_time) > 2:
            self.conscious_content = winner
            self.last_broadcast_time = now
            logger.info(f"GWT: Broadcasting {winner['topic']} to workspace (salience: {winner['salience']:.2f})")
            
            # Prepare serializable data for broadcast
            broadcast_data = winner["data"]
            if hasattr(broadcast_data, "ListFields"): # Protobuf check
                # We might want to convert to dict or just pass it if the bus allows
                pass

            await self.bus.publish("WORKSPACE_BROADCAST", {
                "topic": winner["topic"],
                "data": str(winner["data"]), # Simplified for now to avoid proto serialization issues in bus if any
                "salience": winner["salience"]
            })
