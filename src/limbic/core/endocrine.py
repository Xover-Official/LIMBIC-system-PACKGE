import asyncio
import logging
from typing import Dict
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class EndocrineOrchestrator:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.baselines = {
            "cortisol": 0.2,
            "oxytocin": 0.5,
            "dopamine": 0.4,
            "serotonin": 0.6,
            "adrenaline": 0.1
        }
        self.hormones = dict(self.baselines)
        
        # Subscriptions
        self.bus.subscribe("STIMULUS", self.handle_stimulus)
        self.bus.subscribe("ENGINE_ACTIVE", self.handle_engine_active)

    async def handle_stimulus(self, request):
        # Example: high threat stimulus increases cortisol and adrenaline
        # request can be a StimulusRequest object or a dict
        metadata = getattr(request, 'metadata', {})
        threat_level = metadata.get('threat_level', 0.0)
        
        if threat_level > 0.7:
            await self.release_hormone("cortisol", 0.1)
            await self.release_hormone("adrenaline", 0.2)

    async def handle_engine_active(self, engine_info):
        name = engine_info["name"]
        level = engine_info["level"]
        if name == "FEAR" and level > 0.5:
            await self.release_hormone("cortisol", 0.05 * level)
            await self.release_hormone("adrenaline", 0.1 * level)
        elif name == "SEEKING" and level > 0.5:
            await self.release_hormone("dopamine", 0.05 * level)
        elif name == "CARE" and level > 0.5:
            await self.release_hormone("oxytocin", 0.05 * level)

    async def release_hormone(self, hormone: str, amount: float):
        if hormone in self.hormones:
            self.hormones[hormone] = max(0.0, min(1.0, self.hormones[hormone] + amount))
            logger.debug(f"Released {hormone}: {self.hormones[hormone]}")

    async def run(self):
        logger.info("EndocrineOrchestrator starting...")
        while True:
            # Decay towards baseline
            for hormone, baseline in self.baselines.items():
                diff = baseline - self.hormones[hormone]
                self.hormones[hormone] += diff * 0.05 # Slow decay
            
            await self.bus.publish("HORMONE_LEVELS", self.hormones)
            await asyncio.sleep(1)
