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
            "energy": 1.0,
            "safety": 1.0,
            "belonging": 0.5,
            "financial_hunger": 0.0
        }
        self.bus.subscribe("STIMULUS", self.on_stimulus)
        self.bus.subscribe("SOCIAL_STATE_SUMMARY", self.on_social_update)
        self.bus.subscribe("EFFORT_REQUIRED", self.on_effort)

    async def on_effort(self, data):
        level = data.get("level", 0.0)
        # Effort depletes energy
        self.drives["energy"] = max(0.0, self.drives["energy"] - (level * 0.05))
        if self.drives["energy"] < 0.2:
            await self.bus.publish("HALT_SIGNAL", {"type": "EXHAUSTION", "severity": 1.0 - self.drives["energy"]})

    async def on_social_update(self, data):
        # High reputation and global trust satisfy belonging drive
        reputation = data.get("reputation", 0.5)
        trust = data.get("global_trust", 0.5)
        satisfaction = (reputation + trust) / 2
        # Shift drive towards 1.0 - satisfaction (where 1.0 is high need)
        target_drive = 1.0 - satisfaction
        self.drives["belonging"] = (self.drives["belonging"] * 0.9) + (target_drive * 0.1)

    async def on_stimulus(self, stimulus):
        metadata = getattr(stimulus, 'metadata', {})
        if not isinstance(metadata, dict):
            metadata = {}

        # Update drives based on stimulus
        if "hunger" in metadata:
            self.drives["hunger"] = max(0.0, self.drives["hunger"] + metadata["hunger"])
        if "financial_hunger" in metadata:
            self.drives["financial_hunger"] = max(0.0, min(1.0, metadata["financial_hunger"]))
        if "safety" in metadata:
            self.drives["safety"] = max(0.0, min(1.0, self.drives["safety"] + metadata["safety"]))
        if "social_inclusion" in metadata:
            self.drives["belonging"] = max(0.0, min(1.0, self.drives["belonging"] - metadata["social_inclusion"]))

    async def run(self, clock=None):
        while True:
            # Natural decay/increase over time
            self.drives["hunger"] += 0.01
            self.drives["thirst"] += 0.02
            self.drives["sleep"] += 0.005
            self.drives["energy"] = min(1.0, self.drives["energy"] + 0.005) # Slow recovery
            self.drives["safety"] -= 0.001 # Baseline anxiety
            self.drives["financial_hunger"] *= 0.95 # Slowly decay if not updated

            
            # Ensure bounds
            for k in self.drives:
                self.drives[k] = max(0.0, min(1.0, self.drives[k]))
            
            await self.bus.publish("DRIVE_UPDATE", self.drives)
            if clock:
                await clock.sleep_tick()
            else:
                await asyncio.sleep(5) # Update every 5 seconds
