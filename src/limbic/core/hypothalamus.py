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
            "safety": 1.0,
            "belonging": 0.5,
            "financial_hunger": 0.0
        }
        self.bus.subscribe("STIMULUS", self.on_stimulus)
        self.bus.subscribe("SOCIAL_STATE_SUMMARY", self.on_social_update)

    async def on_social_update(self, data):
        # High reputation and global trust satisfy belonging drive
        reputation = data.get("reputation", 0.5)
        trust = data.get("global_trust", 0.5)
        satisfaction = (reputation + trust) / 2
        # Shift drive towards 1.0 - satisfaction (where 1.0 is high need)
        target_drive = 1.0 - satisfaction
        self.drives["belonging"] = (self.drives["belonging"] * 0.9) + (target_drive * 0.1)

    async def on_stimulus(self, stimulus):
        if hasattr(stimulus, 'metadata'):
            metadata = stimulus.metadata
        else:
            metadata = stimulus.get("metadata", {})

        # Update drives based on stimulus
        if "hunger" in metadata:
            self.drives["hunger"] = max(0.0, self.drives["hunger"] + metadata["hunger"])
        if "financial_hunger" in metadata:
            self.drives["financial_hunger"] = max(0.0, min(1.0, metadata["financial_hunger"]))
        if "safety" in metadata:
            self.drives["safety"] = max(0.0, min(1.0, self.drives["safety"] + metadata["safety"]))
        if "social_inclusion" in metadata:
            self.drives["belonging"] = max(0.0, min(1.0, self.drives["belonging"] - metadata["social_inclusion"]))

    async def run(self):
        while True:
            # Natural decay/increase over time
            self.drives["hunger"] += 0.01
            self.drives["thirst"] += 0.02
            self.drives["sleep"] += 0.005
            self.drives["safety"] -= 0.001 # Baseline anxiety
            self.drives["financial_hunger"] *= 0.95 # Slowly decay if not updated

            
            # Ensure bounds
            for k in self.drives:
                self.drives[k] = max(0.0, min(1.0, self.drives[k]))
            
            await self.bus.publish("DRIVE_UPDATE", self.drives)
            await asyncio.sleep(5) # Update every 5 seconds
