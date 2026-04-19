import asyncio
import logging
from typing import Dict, Any, List, Set, Optional
from limbic.bus import LimbicBus
from limbic.persistence.sqlite_manager import SQLiteManager

logger = logging.getLogger(__name__)

class SocialMemory:
    """
    Social Memory (Social-03): Graph-based tracking of trust and debt.
    Tracks trust levels, affinity, and social debts/credits.
    """
    def __init__(self, bus: LimbicBus, sql_manager: Optional[SQLiteManager] = None):
        self.bus = bus
        self.sql_manager = sql_manager
        self.nodes: Dict[str, Dict[str, Any]] = {}  # agent_id -> properties
        self.edges: Dict[str, Dict[str, Dict[str, Any]]] = {} # (id1, id2) -> relationship

    async def run(self):
        logger.info("Social Memory starting...")
        
        # Load from DB if available
        if self.sql_manager:
            await self._load_from_db()

        self.bus.subscribe("SOCIAL_TRANSACTION", self.on_transaction)
        self.bus.subscribe("AGENT_MODEL_UPDATED", self.on_agent_update)
        
        while True:
            # Periodically decay debts or update affinities
            await self._maintain_memory()
            # Save to DB periodically
            if self.sql_manager:
                await self._save_to_db()
            await asyncio.sleep(60)

    async def _load_from_db(self):
        relationships = await self.sql_manager.get_social_relationships()
        for row in relationships:
            agent_id, trust, affinity, debt, interactions, _ = row
            self._ensure_agent(agent_id)
            rel = self.edges["self"][agent_id]
            rel["trust"] = trust
            rel["affinity"] = affinity
            rel["debt"] = debt
            rel["interactions"] = interactions

    async def _save_to_db(self):
        for agent_id, rel in self.edges.get("self", {}).items():
            await self.sql_manager.update_social_relationship(
                agent_id, 
                rel["trust"], 
                rel["affinity"], 
                rel["debt"], 
                rel["interactions"]
            )

    async def on_transaction(self, data: Dict[str, Any]):
        agent_id = data.get("agent_id")
        type = data.get("type") # "debt", "favor", "betrayal"
        value = data.get("value", 0.0)
        
        if not agent_id:
            return

        self._ensure_agent(agent_id)
        rel = self._get_relationship("self", agent_id)
        rel["interactions"] += 1
        if type == "favor":
            rel["debt"] -= value
            rel["trust"] += value * 0.1
        elif type == "debt":
            rel["debt"] += value
        elif type == "betrayal":
            rel["trust"] -= value * 0.5
            rel["affinity"] -= value * 0.3
            
        rel["trust"] = max(-1.0, min(1.0, rel["trust"]))
        rel["affinity"] = max(-1.0, min(1.0, rel["affinity"]))

        await self.bus.publish("RELATIONSHIP_UPDATED", {
            "agent_id": agent_id,
            "trust": rel["trust"],
            "affinity": rel["affinity"],
            "debt": rel["debt"]
        })

    async def on_agent_update(self, data: Dict[str, Any]):
        agent_id = data.get("agent_id")
        intents = data.get("intents", {})
        
        if not agent_id:
            return
            
        self._ensure_agent(agent_id)
        rel = self._get_relationship("self", agent_id)
        
        # Update trust based on cooperativeness from TPJ
        cooperative_prob = intents.get("cooperative", 0.33)
        rel["trust"] = (rel["trust"] * 0.9) + (cooperative_prob * 2 - 1) * 0.1
        rel["trust"] = max(-1.0, min(1.0, rel["trust"]))

    def _ensure_agent(self, agent_id: str):
        if agent_id not in self.nodes:
            self.nodes[agent_id] = {"id": agent_id}
        if "self" not in self.edges:
            self.edges["self"] = {}
        if agent_id not in self.edges["self"]:
            self.edges["self"][agent_id] = {
                "trust": 0.0,
                "affinity": 0.0,
                "debt": 0.0,
                "interactions": 0
            }

    def _get_relationship(self, id1: str, id2: str):
        return self.edges[id1][id2]

    async def _maintain_memory(self):
        # Decay trust towards 0 if no interactions
        # Decay debt towards 0
        for target_id, rel in self.edges.get("self", {}).items():
            rel["debt"] *= 0.99
            rel["trust"] *= 0.999
            rel["affinity"] *= 0.999
