import asyncio
from limbic.bus import LimbicBus

class FearEngine:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.activation = 0.0
        self.bus.subscribe("EMOTION_EVOKED", self.on_emotion)

    async def on_emotion(self, emotion):
        if emotion["type"] == "FEAR":
            self.activation = max(self.activation, emotion["arousal"])

    async def run(self):
        while True:
            self.activation *= 0.8 # Rapid decay compared to seeking
            if self.activation > 0.3:
                await self.bus.publish("ENGINE_ACTIVE", {"name": "FEAR", "level": self.activation})
            await asyncio.sleep(1)
