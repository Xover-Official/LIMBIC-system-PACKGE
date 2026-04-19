import asyncio
import logging
import numpy as np
from typing import Any, Dict, Optional
from ..registry import ToolRegistry
from ..subcortical.cerebellum import Cerebellum

logger = logging.getLogger(__name__)

class MotorCortex:
    def __init__(self, bus, registry: ToolRegistry, cerebellum: Cerebellum):
        self.bus = bus
        self.registry = registry
        self.cerebellum = cerebellum
        self.noise_level = 0.01
        
        self.bus.subscribe("ACTION_COMMAND", self.handle_action_command)
        self.bus.subscribe("HABIT_SUGGESTION", self.handle_habit_suggestion)
        self.bus.subscribe("AROUSAL_UPDATE", self.handle_arousal)

    async def handle_arousal(self, data: Dict[str, Any]):
        level = data.get("level", "normal")
        if level == "high":
            self.noise_level = 0.05
        elif level == "low":
            self.noise_level = 0.005
        else:
            self.noise_level = 0.01
        logger.debug(f"MotorCortex updated noise level to {self.noise_level} due to arousal {level}")

    async def handle_action_command(self, command: Dict[str, Any]):
        logger.info(f"MotorCortex received action command: {command}")
        await self.execute_action(command.get("action"), command.get("params", {}))

    async def handle_habit_suggestion(self, suggestion: Dict[str, Any]):
        # Only execute habit if confidence is very high and no recent action command?
        # For simplicity, we'll just log it here or execute if it's high enough
        confidence = suggestion.get("confidence", 0)
        if confidence > 0.9:
            logger.info(f"MotorCortex executing habit: {suggestion.get('action')}")
            await self.execute_action(suggestion.get("action"), suggestion.get("params", {}))

    async def execute_action(self, action: str, params: Dict[str, Any]):
        if not action:
            return

        # 1. Refine parameters using Cerebellum's Inverse Model
        refined_params = self.cerebellum.compensate(action, params)
        
        # 2. Inject probabilistic noise
        noisy_params = self.inject_noise(refined_params)
        
        try:
            # 3. Execute via ToolRegistry
            result = await self.registry.execute(action, noisy_params)
            
            # 4. Publish ACTION_RESULT and ACTION_EXECUTED (for SensoryCortex prediction)
            await self.bus.publish("ACTION_RESULT", {"action": action, "result": result})
            await self.bus.publish("ACTION_EXECUTED", {"action": action, "params": noisy_params})
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            await self.bus.publish("ACTION_FAILURE", {"action": action, "error": str(e)})

    def inject_noise(self, params: Dict[str, Any]) -> Dict[str, Any]:
        noisy_params = params.copy()
        for k, v in noisy_params.items():
            if isinstance(v, (int, float)):
                # Add Gaussian noise
                noise = np.random.normal(0, self.noise_level * (abs(v) if v != 0 else 1.0))
                noisy_params[k] = v + noise
        return noisy_params
