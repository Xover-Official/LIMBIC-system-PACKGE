import asyncio
import logging
import numpy as np
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class OFC:
    """
    Orbitofrontal Cortex: Bayesian value learner and utility calculator.
    Uses multi-armed bandit style estimation for candidate plans.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        # Simple action-value map (Bayesian prior)
        self.action_values = {
            "OBSERVE": {"mu": 0.1, "sigma": 0.1},
            "EXPLORE": {"mu": 0.5, "sigma": 0.2},
            "DEFEND": {"mu": -0.1, "sigma": 0.3},
            "COOPERATE": {"mu": 0.4, "sigma": 0.15},
            "RETREAT": {"mu": -0.2, "sigma": 0.2},
            "STAY": {"mu": 0.0, "sigma": 0.05}
        }
        self.bus.subscribe("PLAN_VETTED", self.calculate_utility)
        self.bus.subscribe("REWARD_RECEIVED", self.update_values)

    async def calculate_utility(self, vetting_data):
        plan = vetting_data["plan"]
        action = plan.get("action")
        pid = vetting_data.get("id")
        
        val_params = self.action_values.get(action, {"mu": 0.0, "sigma": 0.5})
        
        # Expected Utility (EU) Calculation
        # mu is our current mean estimate of utility
        base_utility = val_params["mu"]
        
        # Factor in VMPFC vetting score (moral/social value)
        vetting_score = vetting_data.get("score", 0.5)
        
        # Final Utility calculation
        final_utility = base_utility + (vetting_score * 0.4)
        
        # Severe penalty if not approved by VMPFC
        if not vetting_data.get("approved"):
            final_utility -= 1.5 
            
        logger.info(f"OFC: Expected Utility for {action}: {final_utility:.4f} (Base: {base_utility:.4f}, Vetting: {vetting_score:.4f})")
        
        await self.bus.publish("UTILITY_ASSIGNED", {
            "id": pid,
            "plan": plan, 
            "utility": float(final_utility)
        })

    async def update_values(self, reward_data):
        action = reward_data.get("action")
        reward = reward_data.get("value", 0.0)
        
        if not action: return

        if action not in self.action_values:
            self.action_values[action] = {"mu": 0.0, "sigma": 0.5}

        # Bayesian update (Normal-Normal)
        prior = self.action_values[action]
        obs_sigma = 0.2 # Measurement noise
        
        precision_prior = 1 / max(1e-6, prior["sigma"]**2)
        precision_obs = 1 / (obs_sigma**2)
        
        new_mu = (prior["mu"] * precision_prior + reward * precision_obs) / (precision_prior + precision_obs)
        new_sigma = np.sqrt(1 / (precision_prior + precision_obs))
        
        self.action_values[action] = {"mu": new_mu, "sigma": new_sigma}
        logger.info(f"OFC: Updated values for {action}: mu={new_mu:.4f}, sigma={new_sigma:.4f}")

    async def run(self):
        while True:
            await asyncio.sleep(1)
