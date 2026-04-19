import asyncio
import logging
from typing import Dict, Any, List
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class SelfModel:
    """
    Self-Model ("The I"): Maintains identity, agency, and persistent state.
    """
    def __init__(self, bus: LimbicBus, agent_id: str = "Limbic-0"):
        self.bus = bus
        self.agent_id = agent_id
        self.traits = {"curiosity": 0.8, "caution": 0.4}
        self.current_drives: Dict[str, float] = {}
        self.action_history: List[Dict[str, Any]] = []
        self.narrative = "Idle"
        
        self.bus.subscribe("DRIVE_UPDATE", self.on_drive_update)
        self.bus.subscribe("ACTION_RESULT", self.on_action_result)
        self.bus.subscribe("WORKSPACE_BROADCAST", self.on_workspace_broadcast)

    async def on_drive_update(self, drives):
        self.current_drives = drives
        await self.update_narrative()

    async def on_action_result(self, result):
        self.action_history.append(result)
        if len(self.action_history) > 20:
            self.action_history.pop(0)
        await self.update_narrative()

    async def on_workspace_broadcast(self, broadcast):
        # Update narrative based on what's conscious
        topic = broadcast["topic"]
        if topic == "CONFLICT_DETECTED":
            self.narrative = "Resolving internal conflict"
        elif topic == "EMOTION_EVOKED":
            # Accessing data from string representation if we used str() in gwt.py
            # Or if we passed the object, we check type.
            self.narrative = "Processing emotional stimulus"
        
        await self.publish_self_state()

    async def update_narrative(self):
        if not self.current_drives:
            return
            
        # Simple heuristic narrative
        top_drive = max(self.current_drives, key=self.current_drives.get)
        if self.current_drives.get(top_drive, 0) > 0.7:
            self.narrative = f"Motivated by {top_drive}"
        
        await self.publish_self_state()

    async def publish_self_state(self):
        state = {
            "agent_id": self.agent_id,
            "narrative": self.narrative,
            "traits": self.traits,
            "active_drives": self.current_drives
        }
        await self.bus.publish("SELF_STATE_UPDATE", state)

    async def run(self):
        logger.info("Self-Model starting...")
        while True:
            await self.publish_self_state()
            await asyncio.sleep(5)
