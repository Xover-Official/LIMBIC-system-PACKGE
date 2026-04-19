import asyncio
import logging
import time
from typing import List, Dict, Any
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class MetacognitiveMonitor:
    """
    Metacognitive Monitor (HOT/AST): Monitors cognitive performance and attention.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.effort_history: List[float] = []
        self.failure_history: List[Dict[str, Any]] = []
        self.attention_schema: Dict[str, float] = {} # topic -> focus time
        self.last_broadcast_time = time.time()
        
        self.bus.subscribe("EFFORT_REQUIRED", self.on_effort)
        self.bus.subscribe("ACTION_FAILURE", self.on_failure)
        self.bus.subscribe("WORKSPACE_BROADCAST", self.on_workspace_broadcast)

    async def on_effort(self, data):
        self.effort_history.append(data.get("level", 0.0))
        if len(self.effort_history) > 10:
            self.effort_history.pop(0)

    async def on_failure(self, failure):
        self.failure_history.append(failure)
        if len(self.failure_history) > 5:
            self.failure_history.pop(0)
            
        # If too many failures, request cognitive adjustment
        if len(self.failure_history) >= 3:
            logger.warning("Metacognition: High failure rate detected. Requesting more planning effort.")
            await self.bus.publish("META_ADJUSTMENT", {"target": "DLPFC", "action": "INCREASE_PLANNING_ITERATIONS"})

    async def on_workspace_broadcast(self, broadcast):
        now = time.time()
        duration = now - self.last_broadcast_time
        topic = broadcast["topic"]
        
        self.attention_schema[topic] = self.attention_schema.get(topic, 0) + duration
        self.last_broadcast_time = now

    async def run(self):
        logger.info("Metacognitive Monitor starting...")
        while True:
            # Analyze cognitive load
            if self.effort_history:
                avg_effort = sum(self.effort_history) / len(self.effort_history)
                if avg_effort > 0.8:
                    logger.info("Metacognition: Sustained high effort. Signaling cognitive load.")
                    await self.bus.publish("META_ADJUSTMENT", {"target": "SYSTEM", "action": "REDUCE_SAMPLING_RATE"})
            
            # Publish attention schema for state monitoring
            await self.bus.publish("ATTENTION_SCHEMA_UPDATE", self.attention_schema)
            
            await asyncio.sleep(3)
