import asyncio
from limbic.bus import LimbicBus

class Insula:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.current_drives = {}
        self.bus.subscribe("DRIVE_UPDATE", self.on_drive_update)
        self.bus.subscribe("SOCIAL_PAIN", self.on_social_pain)

    async def on_social_pain(self, data):
        intensity = data.get("intensity", 0.0)
        source = data.get("source", "unknown")
        # Social pain maps to negative valence and increased arousal
        await self.bus.publish("EMOTION_EVOKED", {
            "type": "SOCIAL_DISTRESS",
            "valence": -0.3 * intensity,
            "arousal": 0.2 * intensity,
            "source": f"insula_social_pain_{source}"
        })
        await self.bus.publish("INTERNAL_FEELING", ["REJECTED" if intensity > 0.5 else "UNCOMFORTABLE"])

    async def on_drive_update(self, drives):
        self.current_drives = drives
        # Translate drives into feelings
        feelings = []
        if drives.get("hunger", 0) > 0.7:
            feelings.append("HUNGRY")
        if drives.get("safety", 1) < 0.3:
            feelings.append("ANXIOUS")
            
        if feelings:
            await self.bus.publish("INTERNAL_FEELING", feelings)
            # High arousal if drives are critical
            if any(v > 0.8 for v in drives.values()) or drives.get("safety", 1) < 0.2:
                 await self.bus.publish("EMOTION_EVOKED", {"type": "PANIC", "valence": -0.5, "arousal": 0.8})
