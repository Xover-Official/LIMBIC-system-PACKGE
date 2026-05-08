import logging
import asyncio
from typing import Dict
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class PersonalitySystem:
    """
    Big Five Personality Traits implementation:
    - Openness: Affects seeking drive baseline and exploration utility.
    - Conscientiousness: Affects effort allocation and goal persistence.
    - Extraversion: Affects social belonging drive and social reward sensitivity.
    - Agreeableness: Affects cooperation utility and empathy resonance.
    - Neuroticism: Affects fear sensitivity and baseline anxiety.
    """
    def __init__(self, bus: LimbicBus, traits: Dict[str, float] = None):
        self.bus = bus
        self.traits = traits or {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5
        }

    async def run(self):
        logger.info(f"PersonalitySystem starting with traits: {self.traits}")
        while True:
            # Periodically broadcast personality to influence other modules
            await self.bus.publish("PERSONALITY_STATE", self.traits)
            await asyncio.sleep(10)

    def get_trait(self, trait: str) -> float:
        return self.traits.get(trait, 0.5)
