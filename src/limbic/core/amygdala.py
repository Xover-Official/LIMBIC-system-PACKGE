import asyncio
from limbic.bus import LimbicBus

class Amygdala:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.traits = {}
        self.bus.subscribe("STIMULUS", self.on_stimulus)
        self.bus.subscribe("DRIVE_UPDATE", self.on_drive_update)
        self.bus.subscribe("PERSONALITY_STATE", self.on_personality)

    async def on_personality(self, traits):
        self.traits = traits

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
        
        # Handle both Stimulus (old) and StimulusRequest (new)
        content = getattr(stimulus, 'content', "")
        metadata = getattr(stimulus, 'metadata', {})

        # Pull valence/arousal from metadata if it's a StimulusRequest from webhook or new examples
        if "valence" in metadata: valence = metadata["valence"]
        if "arousal" in metadata: arousal = metadata["arousal"]

        # Adjust sensitivity based on personality (Neuroticism increases fear response)
        neuroticism = self.traits.get("neuroticism", 0.5)

        if "threat" in content.lower() or metadata.get("threat_level", 0) > (0.6 - (neuroticism * 0.2)):
            valence = -0.8
            arousal = 0.8 + (neuroticism * 0.2)
            await self.bus.publish("EMOTION_EVOKED", {"type": "FEAR", "valence": valence, "arousal": arousal})
        elif "reward" in stimulus.content.lower():
            # Extraversion increases reward sensitivity
            extraversion = self.traits.get("extraversion", 0.5)
            valence = 0.5 + (extraversion * 0.2)
            arousal = 0.3 + (extraversion * 0.2)
            await self.bus.publish("EMOTION_EVOKED", {"type": "SEEKING", "valence": valence, "arousal": arousal})
            
        source = getattr(stimulus, 'source', 'unknown')
        await self.bus.publish("SIGNIFICANCE_EVALUATED", {"valence": valence, "arousal": arousal, "source": source})
