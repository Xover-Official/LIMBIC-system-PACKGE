import asyncio
import logging
from typing import Dict, Any
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class MirrorNeuronSystem:
    """
    Mirror Neuron System (Social-02): Empathy through simulation.
    Maps observed stimuli of others to internal emotional states.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        # Mapping observed emotions to internal resonance
        self.resonance_factors = {
            "distress": 0.7,
            "joy": 0.5,
            "anger": 0.4,
            "fear": 0.6,
            "sadness": 0.5,
            "pain": 0.8,
            "surprise": 0.3
        }

    async def run(self):
        logger.info("Mirror Neuron System starting...")
        self.bus.subscribe("SOCIAL_OBSERVATION", self.on_observation)
        
        while True:
            await asyncio.sleep(1)

    async def on_observation(self, data: Dict[str, Any]):
        observed_state = data.get("observed_state", {})
        agent_id = data.get("agent_id")
        
        if not observed_state:
            return

        # Resonate with observed emotions
        for emotion, intensity in observed_state.items():
            if emotion in self.resonance_factors:
                resonance = intensity * self.resonance_factors[emotion]
                if resonance > 0.1:
                    logger.debug(f"Mirror resonance: {emotion} at {resonance} from {agent_id}")
                    await self.bus.publish("EMOTION_EVOKED", {
                        "source": f"mirror_neurons_{agent_id}",
                        "emotion": emotion,
                        "intensity": resonance,
                        "valence_shift": self._get_valence_shift(emotion, resonance)
                    })

    def _get_valence_shift(self, emotion: str, intensity: float) -> float:
        negative_emotions = ["distress", "anger", "fear", "sadness", "pain"]
        if emotion in negative_emotions:
            return -intensity * 0.5
        if emotion == "joy":
            return intensity * 0.5
        return 0.0
