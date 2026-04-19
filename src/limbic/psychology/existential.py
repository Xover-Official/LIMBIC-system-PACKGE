import asyncio
import logging
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class ExistentialLayer:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.meaning = 0.5
        self.purpose = 0.5
        self.dread = 0.0
        
        self.bus.subscribe("STIMULUS", self.handle_stimulus)
        self.bus.subscribe("ACTION_RESULT", self.handle_action_result)

    async def handle_stimulus(self, request):
        metadata = getattr(request, 'metadata', {})
        threat_level = metadata.get('threat_level', 0.0)
        if threat_level > 0.8:
            # High threat lowers meaning if frequent
            self.meaning = max(0.0, self.meaning - 0.01)

    async def handle_action_result(self, result):
        # result is a dict
        status = result.get("status")
        if status == "COMPLETED":
            self.purpose = min(1.0, self.purpose + 0.05)
            self.meaning = min(1.0, self.meaning + 0.02)
        elif status == "FAILED":
            self.purpose = max(0.0, self.purpose - 0.05)

    async def run(self):
        logger.info("ExistentialLayer starting...")
        while True:
            # Existential Dread calculation
            # High threat (implied by low meaning/purpose)
            if self.meaning < 0.2 and self.purpose < 0.2:
                self.dread = min(1.0, self.dread + 0.1)
            else:
                self.dread = max(0.0, self.dread - 0.05)
            
            if self.dread > 0.7:
                logger.warning("EXISTENTIAL DREAD ACTIVE")
                await self.bus.publish("EXISTENTIAL_DREAD", {"level": self.dread})
            
            await self.bus.publish("EXISTENTIAL_STATE", {
                "meaning": self.meaning,
                "purpose": self.purpose,
                "dread": self.dread
            })
            await asyncio.sleep(2)
