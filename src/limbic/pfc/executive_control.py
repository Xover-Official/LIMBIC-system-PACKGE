import asyncio
import logging
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class ExecutiveControl:
    """
    Final decision layer that can override limbic impulses 
    based on PFC evaluations.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.current_utility = 0.0
        self.bus.subscribe("UTILITY_ASSIGNED", self.on_utility_assigned)
        self.bus.subscribe("CONFLICT_DETECTED", self.on_conflict)
        self.bus.subscribe("HALT_SIGNAL", self.on_halt_signal)

    async def on_halt_signal(self, halt_data):
        if self.current_utility > 0.7:
            logger.info(f"ExecutiveControl: High utility goal active ({self.current_utility:.2f}). Overriding HALT signal: {halt_data['type']}")
            await self.bus.publish("BLOCK_HALT", {"type": halt_data["type"], "reason": "HIGH_PRIORITY_GOAL"})
        else:
            logger.info(f"ExecutiveControl: Deferring to HALT signal: {halt_data['type']}")

    async def on_utility_assigned(self, data):
        plan = data["plan"]
        utility = data["utility"]
        self.current_utility = utility
        
        if utility > 0.5:
            logger.info(f"ExecutiveControl: Executing plan {plan['action']} with utility {utility:.4f}")
            await self.bus.publish("ACTION_COMMAND", {"action": plan["action"], "source": "PFC"})
            # If there's a conflicting limbic signal, this effectively overrides it
            await self.bus.publish("LIMBIC_OVERRIDE", {"blocked": ["FEAR", "PANIC"], "reason": "HIGH_GOAL_UTILITY"})
        else:
            logger.info(f"ExecutiveControl: Plan {plan['action']} has low utility {utility:.4f}, deferring to limbic system.")

    async def on_conflict(self, conflict_data):
        logger.info(f"ExecutiveControl: Mediating conflict: {conflict_data['reason']}")

    async def run(self):
        while True:
            await asyncio.sleep(1)
