import asyncio
import logging
from typing import Dict, Any, List
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class CulturalNorms:
    """
    Cultural Norm Acquisition (Social-04): Tracks observed behaviors.
    Applies conformity bias to action utility evaluations.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.context_norms: Dict[str, Dict[str, float]] = {} # context -> {action: frequency}
        self.conformity_bias = 0.3

    async def run(self):
        logger.info("Cultural Norms starting...")
        self.bus.subscribe("SOCIAL_OBSERVATION", self.on_observation)
        self.bus.subscribe("PLAN_EVALUATED", self.apply_conformity_bias)
        
        while True:
            await asyncio.sleep(1)

    async def on_observation(self, data: Dict[str, Any]):
        action = data.get("action")
        context = data.get("context_type", "general")
        
        if not action:
            return

        if context not in self.context_norms:
            self.context_norms[context] = {}
        
        # Incremental average of frequency
        self.context_norms[context][action] = self.context_norms[context].get(action, 0) + 1
        
        # Publish norm update
        await self.bus.publish("NORM_UPDATED", {
            "context": context,
            "norms": self.context_norms[context]
        })

    async def apply_conformity_bias(self, data: Dict[str, Any]):
        # Intercept plan evaluation to shift utility based on norms
        action = data.get("action")
        context = data.get("context_type", "general")
        original_utility = data.get("utility", 0.0)
        
        if context in self.context_norms:
            norms = self.context_norms[context]
            total_obs = sum(norms.values())
            if total_obs > 0:
                frequency = norms.get(action, 0) / total_obs
                # Shift utility towards 1.0 if it's a common action
                norm_utility = (frequency * 2 - 1) # -1 to 1
                new_utility = original_utility + (norm_utility * self.conformity_bias)
                new_utility = max(0.0, min(1.0, new_utility))
                
                if abs(new_utility - original_utility) > 0.01:
                    await self.bus.publish("PLAN_ADJUSTED_BY_NORM", {
                        "action": action,
                        "original_utility": original_utility,
                        "new_utility": new_utility
                    })
