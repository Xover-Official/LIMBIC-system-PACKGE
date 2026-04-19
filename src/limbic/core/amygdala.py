import asyncio
from limbic.bus import LimbicBus

class Amygdala:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.bus.subscribe("STIMULUS", self.on_stimulus)
        self.bus.subscribe("DRIVE_UPDATE", self.on_drive_update)

    async def on_drive_update(self, drives):
        # HALT (Hunger, Anger, Loneliness, Tiredness)
        # Anger and Loneliness are not in Hypothalamus yet, but Hunger and Tiredness (sleep) are.
        if drives.get("hunger", 0) > 0.8:
            await self.bus.publish("HALT_SIGNAL", {"type": "HUNGER", "severity": drives["hunger"]})
        if drives.get("sleep", 0) > 0.8:
            await self.bus.publish("HALT_SIGNAL", {"type": "TIREDNESS", "severity": drives["sleep"]})

    async def on_stimulus(self, stimulus):
        # Fast-path valence check
        # For now, simple rule-based evaluation
        valence = 0.0
        arousal = 0.0
        
        if "threat" in stimulus.content.lower() or stimulus.metadata.get("threat_level", 0) > 0.5:
            valence = -0.8
            arousal = 0.9
            await self.bus.publish("EMOTION_EVOKED", {"type": "FEAR", "valence": valence, "arousal": arousal})
        elif "reward" in stimulus.content.lower():
            valence = 0.6
            arousal = 0.4
            await self.bus.publish("EMOTION_EVOKED", {"type": "SEEKING", "valence": valence, "arousal": arousal})
            
        await self.bus.publish("SIGNIFICANCE_EVALUATED", {"valence": valence, "arousal": arousal, "source": stimulus.source})
