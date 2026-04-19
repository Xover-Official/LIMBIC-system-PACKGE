import asyncio
from limbic.bus import LimbicBus

class SeekingEngine:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.activation = 0.2
        self.bus.subscribe("DOPAMINE_SURGE", self.on_dopamine)
        self.bus.subscribe("STIMULUS", self.on_stimulus)

    async def on_dopamine(self, surge):
        self.activation = min(1.0, self.activation + surge["magnitude"])

    async def on_stimulus(self, stimulus):
        # Novelty triggers seeking
        if "novelty" in stimulus.metadata:
            self.activation = min(1.0, self.activation + stimulus.metadata["novelty"])

    async def run(self):
        while True:
            self.activation *= 0.95 # Decay
            if self.activation > 0.5:
                await self.bus.publish("ENGINE_ACTIVE", {"name": "SEEKING", "level": self.activation})
            await asyncio.sleep(2)
