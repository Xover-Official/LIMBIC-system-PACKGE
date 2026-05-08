import asyncio
import time
import logging

logger = logging.getLogger(__name__)

class SimulationClock:
    def __init__(self, tick_rate: float = 1.0, simulation_speed: float = 1.0):
        self.tick_rate = tick_rate # Base seconds per tick
        self.simulation_speed = simulation_speed
        self.paused = False
        self.auto_throttle_factor = 1.0

    def set_speed(self, speed: float):
        self.simulation_speed = max(0.1, speed)
        logger.info(f"Simulation speed set to {self.simulation_speed}")

    def set_pause(self, paused: bool):
        self.paused = paused
        logger.info(f"Simulation {'paused' if paused else 'resumed'}")

    def set_throttle(self, factor: float):
        self.auto_throttle_factor = max(1.0, factor)

    async def sleep_tick(self):
        """Sleep for one simulation tick, adjusted by speed and throttling."""
        while self.paused:
            await asyncio.sleep(0.5)

        base_sleep = self.tick_rate / self.simulation_speed
        actual_sleep = base_sleep * self.auto_throttle_factor
        await asyncio.sleep(actual_sleep)

    def adjust_time(self, seconds: float) -> float:
        """Adjusts a duration based on simulation speed."""
        return seconds / self.simulation_speed
