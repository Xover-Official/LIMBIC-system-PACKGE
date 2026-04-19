import asyncio
import logging
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class VMPFC:
    """
    Ventromedial Prefrontal Cortex: Social and moral evaluation, 
    risk assessment, and emotion regulation.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.moral_constraints = [
            "harm_none",
            "cooperate_first",
            "be_efficient"
        ]
        self.bus.subscribe("PLAN_GENERATED", self.evaluate_plan)

    async def evaluate_plan(self, plan):
        logger.info(f"VMPFC: Evaluating plan: {plan}")
        
        # Simple moral/social logic filter
        is_safe = True
        if plan.get("action") == "ATTACK": # Just an example
             is_safe = False
             
        if is_safe:
            await self.bus.publish("PLAN_VETTED", {"plan": plan, "approved": True})
        else:
            logger.warning(f"VMPFC: Blocked unsafe plan: {plan}")
            await self.bus.publish("PLAN_VETTED", {"plan": plan, "approved": False, "reason": "VIOLATES_SOCIAL_NORMS"})

    async def run(self):
        while True:
            await asyncio.sleep(1)
