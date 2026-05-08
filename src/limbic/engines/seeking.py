import asyncio
from limbic.bus import LimbicBus

class SeekingEngine:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.activation = 0.2
        self.suppressed = False
        self.bus.subscribe("DOPAMINE_SURGE", self.on_dopamine)
        self.bus.subscribe("STIMULUS", self.on_stimulus)
        self.bus.subscribe("LIMBIC_OVERRIDE", self.on_override)

    async def on_dopamine(self, surge):
        increment = surge["magnitude"]
        if self.suppressed:
            increment *= 0.2
        self.activation = min(1.0, self.activation + increment)

    async def on_stimulus(self, stimulus):
        # Novelty triggers seeking
        metadata = getattr(stimulus, 'metadata', {})
        if not isinstance(metadata, dict):
            metadata = {}
        if "novelty" in metadata:
            increment = metadata["novelty"]
            if self.suppressed:
                increment *= 0.1
            self.activation = min(1.0, self.activation + increment)

    async def on_override(self, override):
        if "SEEKING" in override.get("suppress", []):
            self.suppressed = True
            self.activation *= 0.7
        else:
            self.suppressed = False

    async def run(self):
        while True:
            self.activation *= 0.95 # Slow decay
            if self.activation > 0.4:
                await self.bus.publish("ENGINE_ACTIVE", {"name": "SEEKING", "level": self.activation})
            await asyncio.sleep(2)
