import asyncio
from limbic.bus import LimbicBus

class NucleusAccumbens:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.expected_reward = 0.5
        self.bus.subscribe("SIGNIFICANCE_EVALUATED", self.on_evaluation)

    async def on_evaluation(self, evaluation):
        actual_reward = evaluation.get("valence", 0)
        if evaluation.get("arousal", 0) > 0.5:
            rpe = actual_reward - self.expected_reward
            self.expected_reward += 0.1 * rpe # Simple learning rate
            
            await self.bus.publish("REWARD_PREDICTION_ERROR", {"rpe": rpe, "expected": self.expected_reward})
            if rpe > 0.2:
                await self.bus.publish("DOPAMINE_SURGE", {"magnitude": rpe})
