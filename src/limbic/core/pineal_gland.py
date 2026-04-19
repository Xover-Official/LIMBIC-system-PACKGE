import asyncio
import logging
import time
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class PinealGland:
    """
    Biomimetic Pineal Gland: Regulates circadian rhythms via Melatonin.
    Influences arousal and 'sleep' states of the analog.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.melatonin = 0.1
        self.circadian_phase = 0.0 # 0.0 to 2*PI
        self.start_time = time.time()

    async def run(self):
        logger.info("PinealGland starting...")
        while True:
            # Simulate a 24-minute cycle as a 'day' for the daemon
            elapsed = time.time() - self.start_time
            day_length_seconds = 24 * 60 
            self.circadian_phase = (elapsed % day_length_seconds) / day_length_seconds * 2 * 3.14159
            
            # Melatonin peaks at night (PI to 2*PI)
            import math
            # Shifted sine wave so it's high at "night"
            light_level = (math.cos(self.circadian_phase) + 1) / 2 # 1 at "noon", 0 at "midnight"
            self.melatonin = 1.0 - light_level
            
            await self.bus.publish("PINEAL_STATE", {
                "melatonin": self.melatonin,
                "circadian_phase": self.circadian_phase,
                "is_night": light_level < 0.3
            })
            
            # Publish to hormone levels as well
            await self.bus.publish("HORMONE_RELEASE", {"hormone": "melatonin", "amount": self.melatonin})
            
            await asyncio.sleep(5)
