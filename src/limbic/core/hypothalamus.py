import asyncio
import time
from limbic.bus import LimbicBus

class Hypothalamus:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.drives = {
            "hunger": 0.0,
            "thirst": 0.0,
            "sleep": 0.0,
            "safety": 1.0
        }
        self.bus.subscribe("STIMULUS", self.on_stimulus)

    async def on_stimulus(self, stimulus):
        # Update drives based on stimulus
        if "hunger" in stimulus.metadata:
            self.drives["hunger"] = max(0.0, self.drives["hunger"] + stimulus.metadata["hunger"])
        if "safety" in stimulus.metadata:
            self.drives["safety"] = max(0.0, min(1.0, self.drives["safety"] + stimulus.metadata["safety"]))

    async def run(self):
        while True:
            # Natural decay/increase over time
            self.drives["hunger"] += 0.01
            self.drives["thirst"] += 0.02
            self.drives["sleep"] += 0.005
            self.drives["safety"] -= 0.001 # Baseline anxiety
            
            # Ensure bounds
            for k in self.drives:
                self.drives[k] = max(0.0, min(1.0, self.drives[k]))
            
            await self.bus.publish("DRIVE_UPDATE", self.drives)
            await asyncio.sleep(5) # Update every 5 seconds
