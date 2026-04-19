import asyncio
import logging
from typing import Dict, Any
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class ReputationManagement:
    """
    Reputation Management: Models the agent's "social self."
    Interacts with the Insula to translate social status drops into "social pain".
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.reputation = 0.5 # 0 to 1
        self.social_standing = {} # group_id -> score
        self.self_concept = {
            "competence": 0.5,
            "likability": 0.5,
            "integrity": 0.5
        }

    async def run(self):
        logger.info("Reputation Management starting...")
        self.bus.subscribe("SOCIAL_FEEDBACK", self.on_feedback)
        self.bus.subscribe("RELATIONSHIP_UPDATED", self.on_relationship_update)
        
        while True:
            # Slow integration of social feedback into self-concept
            await asyncio.sleep(10)

    async def on_feedback(self, data: Dict[str, Any]):
        sentiment = data.get("sentiment", 0.0) # -1 to 1
        source = data.get("source")
        impact = data.get("impact", 0.1)
        
        old_reputation = self.reputation
        self.reputation += sentiment * impact
        self.reputation = max(0.0, min(1.0, self.reputation))
        
        if self.reputation < old_reputation:
            # Social Pain
            loss = old_reputation - self.reputation
            await self.bus.publish("SOCIAL_PAIN", {
                "intensity": loss * 5.0, # Scale for Insula
                "source": "reputation_loss",
                "feedback_source": source
            })
            
        await self.bus.publish("REPUTATION_UPDATED", {
            "reputation": self.reputation,
            "self_concept": self.self_concept
        })

    async def on_relationship_update(self, data: Dict[str, Any]):
        # If many people trust us, our reputation goes up
        trust = data.get("trust", 0.0)
        affinity = data.get("affinity", 0.0)
        
        # Weighted update to reputation
        self.reputation = (self.reputation * 0.95) + (max(0.0, trust) * 0.03) + (max(0.0, affinity) * 0.02)
        self.reputation = max(0.0, min(1.0, self.reputation))
        
        # Update self-concept based on relationships
        if trust > 0.5:
            self.self_concept["integrity"] = (self.self_concept["integrity"] * 0.99) + 0.01
        elif trust < -0.5:
            self.self_concept["integrity"] = (self.self_concept["integrity"] * 0.99) - 0.01
            
        if affinity > 0.5:
            self.self_concept["likability"] = (self.self_concept["likability"] * 0.99) + 0.01
        elif affinity < -0.5:
            self.self_concept["likability"] = (self.self_concept["likability"] * 0.99) - 0.01
            
        for k in self.self_concept:
            self.self_concept[k] = max(0.0, min(1.0, self.self_concept[k]))
