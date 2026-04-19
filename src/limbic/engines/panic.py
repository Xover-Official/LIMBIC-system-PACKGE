import asyncio
from limbic.bus import LimbicBus

class PanicEngine:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.activation = 0.0
        self.bus.subscribe("EMOTION_EVOKED", self.on_emotion)

    async def on_emotion(self, emotion):
        if emotion["type"] == "PANIC":
            self.activation = max(self.activation, emotion["arousal"])

    async def run(self):
        while True:
            self.activation *= 0.9
            if self.activation > 0.4:
                await self.bus.publish("ENGINE_ACTIVE", {"name": "PANIC", "level": self.activation})
            await asyncio.sleep(1)
