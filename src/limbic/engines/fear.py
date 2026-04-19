import asyncio
from limbic.bus import LimbicBus

class FearEngine:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.activation = 0.0
        self.suppressed = False
        self.hormone_modulation = 1.0
        self.bus.subscribe("EMOTION_EVOKED", self.on_emotion)
        self.bus.subscribe("LIMBIC_OVERRIDE", self.on_override)
        self.bus.subscribe("HORMONE_LEVELS", self.on_hormones)

    async def on_hormones(self, hormones):
        # Cortisol increases fear sensitivity, Oxytocin decreases it
        self.hormone_modulation = 1.0 + hormones.get("cortisol", 0.0) - (hormones.get("oxytocin", 0.0) * 0.5)

    async def on_emotion(self, emotion):
        if emotion["type"] == "FEAR":
            new_activation = max(self.activation, emotion["arousal"] * self.hormone_modulation)
            if self.suppressed:
                self.activation = new_activation * 0.3
            else:
                self.activation = new_activation

    async def on_override(self, override):
        if "FEAR" in override.get("suppress", []):
            self.suppressed = True
            self.activation *= 0.4
        else:
            self.suppressed = False

    async def run(self):
        while True:
            self.activation *= 0.8 # Rapid decay
            if self.activation > 0.3:
                await self.bus.publish("ENGINE_ACTIVE", {"name": "FEAR", "level": self.activation})
            await asyncio.sleep(1)
