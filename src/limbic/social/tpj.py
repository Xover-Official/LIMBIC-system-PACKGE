import asyncio
import logging
from typing import Dict, Any, List
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class TPJ:
    """
    Temporoparietal Junction (Social-01): Bayesian Theory of Mind.
    Tracks other agents' intentions and beliefs based on observed actions.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.agent_models: Dict[str, Dict[str, Any]] = {}
        # Prior probabilities for intentions
        self.intent_priors = {
            "cooperative": 0.5,
            "competitive": 0.3,
            "neutral": 0.2
        }
        self.focus_agents: List[str] = []
        self.max_focus = 5

    async def run(self):
        logger.info("TPJ (Theory of Mind) starting...")
        self.bus.subscribe("STIMULUS", self.on_stimulus)
        self.bus.subscribe("SOCIAL_OBSERVATION", self.on_observation)
        self.bus.subscribe("WORKSPACE_BROADCAST", self.on_workspace_broadcast)
        
        while True:
            await asyncio.sleep(1)

    async def on_workspace_broadcast(self, data: Dict[str, Any]):
        # Update focus based on what's in the global workspace
        if data.get("topic") == "SOCIAL_SIGNAL":
            # Extract agent from social signal if present
            # For now just a placeholder
            pass

    async def on_stimulus(self, data: Any):
        # Data might contain social information embedded in stimulus
        source = None
        if hasattr(data, 'source'):
            source = data.source
        elif isinstance(data, dict):
            source = data.get("source")
            
        if source:
            await self._process_social_signal(source, data)

    async def on_observation(self, data: Dict[str, Any]):
        agent_id = data.get("agent_id")
        action = data.get("action")
        context = data.get("context", {})
        
        if agent_id:
            # Manage focus: if agent is new and we have space, or if it's already in focus
            if agent_id not in self.focus_agents:
                self.focus_agents.append(agent_id)
                if len(self.focus_agents) > self.max_focus:
                    self.focus_agents.pop(0)
            
            await self._update_model(agent_id, action, context)

    async def _process_social_signal(self, agent_id: str, data: Any):
        # Extract intent signals from raw stimulus
        action = None
        if hasattr(data, 'content'):
            action = data.content
        elif isinstance(data, dict):
            action = data.get("content") or data.get("action")
            
        metadata = {}
        if hasattr(data, 'metadata'):
            metadata = data.metadata
        elif isinstance(data, dict):
            metadata = data.get("metadata", {})

        if action:
            await self._update_model(agent_id, action, metadata)

    async def _update_model(self, agent_id: str, action: str, context: Dict[str, Any]):
        if agent_id not in self.agent_models:
            self.agent_models[agent_id] = {
                "beliefs": {},
                "intents": self.intent_priors.copy(),
                "history": []
            }
        
        model = self.agent_models[agent_id]
        model["history"].append({"action": action, "context": context})
        
        # Bayesian Update (Simplified)
        # Likelihood of action given intent
        likelihoods = self._get_likelihoods(action, context)
        
        evidence = 0
        for intent, prob in model["intents"].items():
            evidence += prob * likelihoods.get(intent, 0.1)
        
        if evidence > 0:
            for intent in model["intents"]:
                model["intents"][intent] = (model["intents"][intent] * likelihoods.get(intent, 0.1)) / evidence

        await self.bus.publish("AGENT_MODEL_UPDATED", {
            "agent_id": agent_id,
            "intents": model["intents"]
        })

    def _get_likelihoods(self, action: str, context: Dict[str, Any]) -> Dict[str, float]:
        # Mapping actions to likelihood of intent
        # This would ideally be a more complex mapping
        action = action.lower()
        if any(w in action for w in ["help", "give", "share", "support", "assist"]):
            return {"cooperative": 0.8, "competitive": 0.05, "neutral": 0.15}
        if any(w in action for w in ["attack", "take", "block", "steal", "deceive", "harm"]):
            return {"cooperative": 0.05, "competitive": 0.8, "neutral": 0.15}
        if any(w in action for w in ["observe", "wait", "move", "look"]):
            return {"cooperative": 0.2, "competitive": 0.2, "neutral": 0.6}
        return {"cooperative": 0.33, "competitive": 0.33, "neutral": 0.34}
