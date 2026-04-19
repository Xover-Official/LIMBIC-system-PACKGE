import logging
import json
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class BasalGanglia:
    def __init__(self, bus, habit_file: str = "habits.json"):
        self.bus = bus
        self.habit_file = habit_file
        self.habits: Dict[str, Dict[str, Any]] = self._load_habits()
        self.last_percept: Optional[Dict[str, Any]] = None
        self.last_habit_suggestion: Optional[str] = None
        
        self.bus.subscribe("PERCEPT", self.handle_percept)
        self.bus.subscribe("REWARD_SIGNAL", self.handle_reward)

    def _load_habits(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.habit_file):
            try:
                with open(self.habit_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading habits: {e}")
        return {}

    def _save_habits(self):
        try:
            with open(self.habit_file, 'w') as f:
                json.dump(self.habits, f)
        except Exception as e:
            logger.error(f"Error saving habits: {e}")

    async def handle_percept(self, percept: Dict[str, Any]):
        self.last_percept = percept
        # Simple habit lookup based on some stimulus characteristics
        stimulus_type = percept.get("type", "unknown")
        
        if stimulus_type in self.habits:
            habit = self.habits[stimulus_type]
            if habit.get("confidence", 0) > 0.7:
                logger.info(f"BasalGanglia suggesting habit for {stimulus_type}")
                self.last_habit_suggestion = habit["action"]
                await self.bus.publish("HABIT_SUGGESTION", {
                    "action": habit["action"],
                    "params": habit.get("params", {}),
                    "confidence": habit.get("confidence", 0)
                })

    async def handle_reward(self, reward_data: Dict[str, Any]):
        reward_value = reward_data.get("value", 0)
        logger.info(f"BasalGanglia received reward: {reward_value}")
        
        # In a real system, we'd need to know which action this reward is for.
        # Here we assume it's for the last habit suggested or last action taken.
        if self.last_percept and self.last_habit_suggestion:
            stimulus_type = self.last_percept.get("type", "unknown")
            if stimulus_type in self.habits:
                # Update confidence based on reward
                current_confidence = self.habits[stimulus_type]["confidence"]
                learning_rate = 0.1
                # Reward is usually 0 to 1, centered at 0.5 for neutral
                new_confidence = current_confidence + learning_rate * (reward_value - 0.5)
                self.habits[stimulus_type]["confidence"] = max(0.0, min(1.0, new_confidence))
                
                logger.debug(f"Updated habit for {stimulus_type}: confidence={self.habits[stimulus_type]['confidence']}")
                self._save_habits()
