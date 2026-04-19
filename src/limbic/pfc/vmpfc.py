import asyncio
import logging
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class VMPFC:
    """
    Ventromedial Prefrontal Cortex: Social and moral evaluation, 
    risk assessment, and emotion regulation.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.moral_norms = {
            "harm_none": 1.0,
            "cooperate": 0.8,
            "honesty": 0.7,
            "reciprocity": 0.6
        }
        self.somatic_markers = {} # Stores emotional associations with actions
        
        self.bus.subscribe("CANDIDATE_PLAN", self.evaluate_candidate)
        self.bus.subscribe("EMOTION_EVOKED", self.on_emotion)
        self.bus.subscribe("INSULA_FEELING", self.on_feeling)

    async def on_emotion(self, emotion_data):
        # Update somatic markers based on current context and emotion
        # Simplified: associate emotion type with the most recent action if we can
        pass

    async def on_feeling(self, feeling):
        # Update current somatic state
        pass

    async def evaluate_candidate(self, candidate):
        action = candidate.get("action")
        pid = candidate.get("id")
        logger.info(f"VMPFC: Evaluating candidate: {action} (ID: {pid})")
        
        # Calculate normative score
        score = 0.5 # Neutral start
        reasons = []
        
        if action == "ATTACK":
            score -= 1.0
            reasons.append("Violates harm_none")
        elif action == "COOPERATE":
            score += 0.3
            reasons.append("Matches cooperate norm")
        elif action == "RETREAT":
            score += 0.1
            reasons.append("Prudent/Safe")
        elif action == "EXPLORE":
            score += 0.2
            reasons.append("Growth-oriented")
            
        # Apply somatic markers (learned associations)
        somatic_bias = self.somatic_markers.get(action, 0.0)
        score += somatic_bias
        
        approved = score > 0.3
        
        await self.bus.publish("PLAN_VETTED", {
            "id": pid,
            "plan": candidate, 
            "approved": approved,
            "score": score,
            "reasons": reasons
        })

    async def run(self):
        while True:
            await asyncio.sleep(1)
