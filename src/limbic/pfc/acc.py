import asyncio
import logging
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class ACC:
    """
    Anterior Cingulate Cortex: Error detection, conflict monitoring, 
    and resource allocation.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.current_emotions = {}
        self.current_plan = None
        
        self.bus.subscribe("EMOTION_EVOKED", self.on_emotion)
        self.bus.subscribe("PLAN_GENERATED", self.on_plan)

    async def on_emotion(self, emotion):
        self.current_emotions[emotion["type"]] = emotion["valence"]
        await self.check_for_conflict()

    async def on_plan(self, plan):
        self.current_plan = plan
        await self.check_for_conflict()

    async def check_for_conflict(self):
        if not self.current_plan:
            return

        action = self.current_plan.get("action")
        
        # Detect conflict between "Bottom-Up" emotion and "Top-Down" plan
        has_conflict = False
        if action == "EXPLORE" and self.current_emotions.get("FEAR", 0) < -0.5:
            has_conflict = True
            conflict_reason = "FEAR vs EXPLORE"
        elif action == "STAY" and self.current_emotions.get("SEEKING", 0) > 0.5:
            has_conflict = True
            conflict_reason = "SEEKING vs STAY"

        if has_conflict:
            logger.warning(f"ACC: Conflict detected: {conflict_reason}")
            await self.bus.publish("CONFLICT_DETECTED", {"reason": conflict_reason, "level": 0.8})
            # Trigger top-down override mechanism if utility is high (handled by a separate module or PFC ensemble)

    async def run(self):
        while True:
            await asyncio.sleep(1)
