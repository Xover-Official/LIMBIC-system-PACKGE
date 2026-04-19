import asyncio
import logging
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class VMPFC:
    """
    Ventromedial Prefrontal Cortex: Social and moral evaluation, 
    risk assessment, and emotion regulation.
    Implements Somatic Marker Theory for impulse control.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.moral_norms = {
            "harm_none": 1.0,
            "cooperate": 0.8,
            "honesty": 0.7,
            "reciprocity": 0.6
        }
        self.somatic_markers = {} # (context_tuple, action) -> valence
        self.last_action_context = None # (context_tuple, action)
        
        self.bus.subscribe("CANDIDATE_PLAN", self.evaluate_candidate)
        self.bus.subscribe("EMOTION_EVOKED", self.on_emotion)
        self.bus.subscribe("INSULA_FEELING", self.on_feeling)
        self.bus.subscribe("ACTION_COMMAND", self.on_action_command)

    async def on_action_command(self, command):
        action = command.get("action")
        # Since we don't have the context in ACTION_COMMAND directly usually,
        # we might need to rely on what was last evaluated or pass context in command.
        # For now, let's assume we store the context during evaluation.
        pass

    async def on_emotion(self, emotion_data):
        # Update somatic markers based on current context and emotion
        valence = emotion_data.get("valence", 0.0)
        if self.last_action_context:
            # Simple reinforcement learning for somatic markers
            old_val = self.somatic_markers.get(self.last_action_context, 0.0)
            self.somatic_markers[self.last_action_context] = old_val + 0.3 * (valence - old_val)
            logger.info(f"VMPFC: Learned somatic marker for {self.last_action_context}: {self.somatic_markers[self.last_action_context]:.2f}")

    async def on_feeling(self, feeling):
        # Update current somatic state
        pass

    async def evaluate_candidate(self, candidate):
        action = candidate.get("action")
        pid = candidate.get("id")
        context = tuple(candidate.get("context", ["idle"]))
        
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
        # Try exact context match
        marker_key = (context, action)
        somatic_bias = self.somatic_markers.get(marker_key, 0.0)
        
        # Also check general action bias if no specific context match
        if marker_key not in self.somatic_markers:
            # Average across all contexts for this action
            biases = [v for k, v in self.somatic_markers.items() if k[1] == action]
            if biases:
                somatic_bias = sum(biases) / len(biases)

        score += somatic_bias
        if somatic_bias < -0.4:
            reasons.append(f"Somatic Veto: Negative association ({somatic_bias:.2f})")
        
        # Veto if score is too low
        approved = score > 0.2
        
        # Record this as the potentially last action context
        self.last_action_context = (context, action)

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
