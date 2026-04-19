import asyncio
import time
import logging
from typing import List, Dict, Any
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class WorkingMemoryItem:
    def __init__(self, content: Any, importance: float = 1.0):
        self.content = content
        self.importance = importance
        self.timestamp = time.time()

    def get_relevance(self, decay_rate: float = 0.1) -> float:
        elapsed = time.time() - self.timestamp
        return self.importance * (2.71828 ** (-decay_rate * elapsed))

class DLPFC:
    """
    Dorsolateral Prefrontal Cortex: Responsible for planning, executive control, 
    and maintaining working memory.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.working_memory: List[WorkingMemoryItem] = []
        self.max_wm_size = 7  # Miller's Law
        self.decay_rate = 0.05
        
        self.bus.subscribe("STIMULUS", self.on_stimulus)
        self.bus.subscribe("CONTEXT_RECALLED", self.on_context_recalled)
        self.bus.subscribe("CONFLICT_DETECTED", self.on_conflict)

    async def on_stimulus(self, stimulus):
        self.add_to_working_memory(stimulus.content, importance=0.8)
        await self.replan()

    async def on_context_recalled(self, contexts):
        for ctx in contexts:
            self.add_to_working_memory(ctx, importance=0.5)
        await self.replan()

    async def on_conflict(self, conflict_data):
        logger.info(f"DLPFC: Conflict detected, increasing effort. {conflict_data}")
        # Scale effort: more iterations in planning
        await self.replan(iterations=20)

    def add_to_working_memory(self, content, importance=1.0):
        self.working_memory.append(WorkingMemoryItem(content, importance))
        # Keep only relevant items and limit size
        self.working_memory = sorted(
            [item for item in self.working_memory if item.get_relevance(self.decay_rate) > 0.1],
            key=lambda x: x.get_relevance(self.decay_rate),
            reverse=True
        )[:self.max_wm_size]

    async def replan(self, iterations=10):
        # MCTS-inspired simplified planning
        # In a real scenario, this would explore possible action sequences
        current_context = [item.content for item in self.working_memory]
        if not current_context:
            return

        logger.info(f"DLPFC: Planning with context: {current_context}")
        
        # Simulate tree search
        best_plan = {"action": "OBSERVE", "confidence": 0.5}
        
        # Logic for choosing action based on context
        if any("threat" in str(c).lower() for c in current_context):
            best_plan = {"action": "DEFEND", "confidence": 0.9}
        elif any("reward" in str(c).lower() for c in current_context):
            best_plan = {"action": "EXPLORE", "confidence": 0.8}

        await self.bus.publish("PLAN_GENERATED", best_plan)

    async def run(self):
        while True:
            # Periodic cleanup of working memory
            self.working_memory = [item for item in self.working_memory if item.get_relevance(self.decay_rate) > 0.1]
            await asyncio.sleep(5)
