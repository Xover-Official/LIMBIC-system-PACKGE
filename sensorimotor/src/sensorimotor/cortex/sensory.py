import logging
import asyncio
from typing import Any, Dict
from ..subcortical.cerebellum import Cerebellum

logger = logging.getLogger(__name__)

class SensoryCortex:
    def __init__(self, bus, cerebellum: Cerebellum):
        self.bus = bus
        self.cerebellum = cerebellum
        self.last_prediction: Dict[str, Any] = {}
        
        # Subscribe to STIMULUS
        self.bus.subscribe("STIMULUS", self.handle_stimulus)
        # We might also need to know when an action was taken to get a prediction
        self.bus.subscribe("ACTION_EXECUTED", self.handle_action_executed)

    async def handle_action_executed(self, data: Dict[str, Any]):
        action = data.get("action")
        params = data.get("params")
        if action and params:
            self.last_prediction = self.cerebellum.predict_outcome(action, params)
            logger.debug(f"SensoryCortex updated prediction based on action: {action}")

    async def handle_stimulus(self, stimulus: Any):
        logger.info(f"SensoryCortex processing stimulus: {stimulus}")
        
        # Normalize stimulus to dict
        if hasattr(stimulus, "metadata"):
            stim_dict = {k: v for k, v in stimulus.metadata.items()}
            stim_dict["source"] = getattr(stimulus, "source", "unknown")
            stim_dict["content"] = getattr(stimulus, "content", "")
            # If type is not in metadata, use source as type
            if "type" not in stim_dict:
                stim_dict["type"] = stim_dict["source"]
        elif isinstance(stimulus, dict):
            stim_dict = stimulus
        else:
            stim_dict = {"raw": stimulus, "type": "unknown"}

        # Calculate Prediction Error (Surprise)
        prediction_error = self.calculate_prediction_error(stim_dict, self.last_prediction)
        
        # Generate Percept
        percept = self.generate_percept(stim_dict, prediction_error)
        
        # Publish PERCEPT and PREDICTION_ERROR
        await self.bus.publish("PERCEPT", percept)
        await self.bus.publish("PREDICTION_ERROR", {
            "error_value": prediction_error,
            "stimulus": stim_dict,
            "prediction": self.last_prediction
        })
        
        # If error is high, might trigger arousal
        if prediction_error > 0.7:
            await self.bus.publish("AROUSAL_UPDATE", {"level": "high", "source": "sensory_surprise"})
            await self.bus.publish("DOPAMINE_SURGE", {"value": prediction_error, "reason": "novelty"})

    def calculate_prediction_error(self, stimulus: Dict[str, Any], prediction: Dict[str, Any]) -> float:
        if not prediction:
            return 1.0 # Maximum surprise if no prediction
        
        # Simple error calculation: count differences in shared keys
        # In a real system, this would be a mathematical distance between vectors
        errors = 0
        total_keys = 0
        for k, v in prediction.items():
            total_keys += 1
            if k not in stimulus or stimulus[k] != v:
                errors += 1
        
        return errors / total_keys if total_keys > 0 else 0.5

    def generate_percept(self, stimulus: Dict[str, Any], prediction_error: float) -> Dict[str, Any]:
        # A percept is a refined interpretation of the stimulus
        percept = stimulus.copy()
        percept["confidence"] = 1.0 - prediction_error
        percept["processed"] = True
        return percept
