import asyncio
import logging
import time
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class AgeLayer:
    """
    Developmental Age Layer: Tracks the 'age' of the human analog.
    As age increases, 'plasticity' (learning rate/flexibility) decays.
    """
    def __init__(self, bus: LimbicBus, initial_age=0.0):
        self.bus = bus
        self.age = initial_age # Years
        self.plasticity = 1.0
        self.birth_time = time.time()

    def calculate_plasticity(self):
        # Plasticity decay formula: P = e^(-age/20)
        # Very high in childhood, slows down but continues to drop
        import math
        return math.exp(-self.age / 25.0)

    async def run(self):
        logger.info("AgeLayer starting...")
        while True:
            # For simulation, 1 year = 1 hour real time
            elapsed_seconds = time.time() - self.birth_time
            self.age = elapsed_seconds / 3600.0
            
            self.plasticity = self.calculate_plasticity()
            
            await self.bus.publish("DEVELOPMENTAL_STATE", {
                "age": self.age,
                "plasticity": self.plasticity,
                "stage": self.get_stage()
            })
            
            await asyncio.sleep(10)

    def get_stage(self):
        if self.age < 2: return "INFANCY"
        if self.age < 12: return "CHILDHOOD"
        if self.age < 20: return "ADOLESCENCE"
        if self.age < 60: return "ADULTHOOD"
        return "SENESCENCE"
