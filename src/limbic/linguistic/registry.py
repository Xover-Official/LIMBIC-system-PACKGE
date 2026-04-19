import logging
from typing import Dict, Any, List
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class SemanticRegistry:
    """
    Semantic Registry (Ling-04): Maps internal concept IDs to shared tokens.
    Enables emergent communication between agents.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.concept_to_token: Dict[str, str] = {}
        self.token_to_concept: Dict[str, str] = {}

    async def run(self):
        logger.info("Semantic Registry starting...")
        self.bus.subscribe("CONCEPT_MAPPING_PROPOSAL", self.handle_proposal)
        self.bus.subscribe("LINGUISTIC_INPUT", self.on_input)

    async def handle_proposal(self, proposal: Dict[str, Any]):
        concept_id = proposal.get("concept_id")
        token = proposal.get("token")
        
        if concept_id and token:
            self.concept_to_token[concept_id] = token
            self.token_to_concept[token] = concept_id
            logger.info(f"Registered semantic mapping: {concept_id} <-> {token}")
            await self.bus.publish("SEMANTIC_MAPPING_UPDATED", {
                "concept_id": concept_id,
                "token": token
            })

    async def on_input(self, data: Dict[str, Any]):
        tokens = data.get("tokens", [])
        concepts = []
        for t in tokens:
            if t in self.token_to_concept:
                concepts.append(self.token_to_concept[t])
        
        if concepts:
            await self.bus.publish("CONCEPTS_DECODED", {"concepts": concepts})
