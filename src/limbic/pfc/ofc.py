import asyncio
import logging
import numpy as np
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class OFC:
    """
    Orbitofrontal Cortex: Represents the value of rewards and punishments 
    expected for different actions.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        # Simple action-value map (Bayesian prior)
        self.action_values = {
            "OBSERVE": {"mu": 0.1, "sigma": 0.1},
            "EXPLORE": {"mu": 0.5, "sigma": 0.2},
            "DEFEND": {"mu": 0.0, "sigma": 0.3},
            "STAY": {"mu": 0.0, "sigma": 0.05}
        }
        self.bus.subscribe("PLAN_VETTED", self.calculate_utility)
        self.bus.subscribe("REWARD_RECEIVED", self.update_values)

    async def calculate_utility(self, vetting_data):
        if not vetting_data.get("approved"):
            return

        plan = vetting_data["plan"]
        action = plan.get("action")
        
        val_params = self.action_values.get(action, {"mu": 0.0, "sigma": 0.5})
        
        # Sample utility using Bayesian approach
        utility = np.random.normal(val_params["mu"], val_params["sigma"])
        
        logger.info(f"OFC: Calculated utility for {action}: {utility:.4f}")
        
        await self.bus.publish("UTILITY_ASSIGNED", {"plan": plan, "utility": float(utility)})

    async def update_values(self, reward_data):
        action = reward_data["action"]
        reward = reward_data["value"]
        
        if action in self.action_values:
            # Simple Bayesian update (Normal-Normal)
            prior = self.action_values[action]
            obs_sigma = 0.1
            
            new_mu = (prior["mu"] / prior["sigma"]**2 + reward / obs_sigma**2) / (1 / prior["sigma"]**2 + 1 / obs_sigma**2)
            new_sigma = np.sqrt(1 / (1 / prior["sigma"]**2 + 1 / obs_sigma**2))
            
            self.action_values[action] = {"mu": new_mu, "sigma": new_sigma}
            logger.info(f"OFC: Updated values for {action}: mu={new_mu:.4f}, sigma={new_sigma:.4f}")

    async def run(self):
        while True:
            await asyncio.sleep(1)
