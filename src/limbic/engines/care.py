import asyncio
from limbic.bus import LimbicBus

class CareEngine:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.activation = 0.0
        self.bus.subscribe("STIMULUS", self.on_stimulus)

    async def on_stimulus(self, stimulus):
        if "social" in stimulus.content.lower() or "friendly" in stimulus.content.lower():
            self.activation = min(1.0, self.activation + 0.3)

    async def run(self):
        while True:
            self.activation *= 0.95
            if self.activation > 0.3:
                await self.bus.publish("ENGINE_ACTIVE", {"name": "CARE", "level": self.activation})
            await asyncio.sleep(3)
