import asyncio
import logging
from typing import Dict, List, Any
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class PsychologicalLattice:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.shadow_reservoir = 0.0
        self.ego_coherence = 1.0
        self.biases = {
            "loss_aversion": 1.5,
            "optimism": 0.2
        }
        
        self.bus.subscribe("LIMBIC_OVERRIDE", self.handle_override)
        self.bus.subscribe("PLAN_VETTED", self.handle_plan_vetted)
        self.bus.subscribe("UTILITY_ASSIGNED", self.apply_biases)

    async def handle_override(self, override):
        # Suppressed drives increase shadow reservoir
        suppress_list = override.get("suppress", [])
        if suppress_list:
            self.shadow_reservoir += 0.1 * len(suppress_list)
            self.ego_coherence -= 0.05
            logger.debug(f"Shadow Reservoir: {self.shadow_reservoir}, Ego Coherence: {self.ego_coherence}")

    async def handle_plan_vetted(self, vetting):
        # Alignment between PFC and drives
        if vetting["approved"]:
            self.ego_coherence = min(1.0, self.ego_coherence + 0.02)
        else:
            self.ego_coherence = max(0.0, self.ego_coherence - 0.02)

    async def apply_biases(self, data):
        # Modifies the utility of plans based on cognitive biases
        utility = data["utility"]
        # Example: Loss aversion makes negative outcomes more significant
        # Here we just apply optimism to positive utilities
        biased_utility = utility * (1.0 + self.biases["optimism"])
        
        # We publish the biased utility so other modules can use it
        await self.bus.publish("BIASED_UTILITY", {"plan": data["plan"], "utility": biased_utility})

    async def run(self):
        logger.info("PsychologicalLattice starting...")
        while True:
            # Shadow Outbursts
            if self.shadow_reservoir > 1.0:
                logger.warning("SHADOW OUTBURST!")
                await self.bus.publish("SHADOW_OUTBURST", {"intensity": self.shadow_reservoir})
                self.shadow_reservoir *= 0.2 # Discharge
            
            # Decay/Recovery
            self.shadow_reservoir = max(0.0, self.shadow_reservoir - 0.01)
            self.ego_coherence = min(1.0, self.ego_coherence + 0.005)
            
            await self.bus.publish("PSYCH_STATE", {
                "shadow": self.shadow_reservoir,
                "ego_coherence": self.ego_coherence
            })
            await asyncio.sleep(1)
