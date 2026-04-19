import asyncio
import logging
from typing import Dict, Any, List, Set, Optional, Union
from limbic.bus import LimbicBus
from limbic.persistence.sqlite_manager import SQLiteManager
from limbic.persistence.postgres_manager import PostgresManager

logger = logging.getLogger(__name__)

class SocialMemory:
    """
    Social Memory (Social-03): Graph-based tracking of trust and debt.
    Tracks trust levels, affinity, and social debts/credits.
    Upgraded for multi-hop reputation graph.
    """
    def __init__(self, bus: LimbicBus, 
                 sql_manager: Optional[SQLiteManager] = None, 
                 pg_manager: Optional[PostgresManager] = None,
                 self_id: str = "self"):
        self.bus = bus
        self.sql_manager = sql_manager
        self.pg_manager = pg_manager
        self.self_id = self_id
        self.nodes: Dict[str, Dict[str, Any]] = {}  # agent_id -> properties
        self.edges: Dict[str, Dict[str, Dict[str, Any]]] = {} # actor_id -> target_id -> relationship

    async def run(self):
        logger.info(f"Social Memory starting as {self.self_id}...")
        
        # Load from DB if available
        await self._load_from_db()

        self.bus.subscribe("SOCIAL_TRANSACTION", self.on_transaction)
        self.bus.subscribe("AGENT_MODEL_UPDATED", self.on_agent_update)
        self.bus.subscribe("REPUTATION_QUERY", self.on_reputation_query)
        
        while True:
            await self._maintain_memory()
            await self._save_to_db()
            await asyncio.sleep(60)

    async def _load_from_db(self):
        if self.pg_manager:
            rows = await self.pg_manager.get_social_relationships(self.self_id)
            for row in rows:
                target_id = row['target_id']
                self._ensure_edge(self.self_id, target_id)
                rel = self.edges[self.self_id][target_id]
                rel["trust"] = row['trust']
                rel["affinity"] = row['affinity']
                rel["debt"] = row['debt']
                rel["interactions"] = row['interactions']
        elif self.sql_manager:
            relationships = await self.sql_manager.get_social_relationships()
            for row in relationships:
                agent_id, trust, affinity, debt, interactions, _ = row
                self._ensure_edge(self.self_id, agent_id)
                rel = self.edges[self.self_id][agent_id]
                rel["trust"] = trust
                rel["affinity"] = affinity
                rel["debt"] = debt
                rel["interactions"] = interactions

    async def _save_to_db(self):
        if self.pg_manager:
            for target_id, rel in self.edges.get(self.self_id, {}).items():
                await self.pg_manager.update_social_relationship(
                    self.self_id,
                    target_id,
                    rel["trust"],
                    rel["affinity"],
                    rel["debt"],
                    rel["interactions"]
                )
        elif self.sql_manager:
            for agent_id, rel in self.edges.get(self.self_id, {}).items():
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

        self._ensure_edge(self.self_id, agent_id)
        rel = self.edges[self.self_id][agent_id]
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
            
        self._ensure_edge(self.self_id, agent_id)
        rel = self.edges[self.self_id][agent_id]
        
        # Update trust based on cooperativeness from TPJ
        cooperative_prob = intents.get("cooperative", 0.33)
        rel["trust"] = (rel["trust"] * 0.9) + (cooperative_prob * 2 - 1) * 0.1
        rel["trust"] = max(-1.0, min(1.0, rel["trust"]))

    async def on_reputation_query(self, data: Dict[str, Any]):
        target_id = data.get("target_id")
        # Multi-hop trust calculation (simple version)
        trust = self._calculate_multi_hop_trust(self.self_id, target_id)
        await self.bus.publish("REPUTATION_RESULT", {
            "target_id": target_id,
            "calculated_trust": trust
        })

    def _calculate_multi_hop_trust(self, source_id: str, target_id: str, max_depth: int = 2) -> float:
        if source_id == target_id: return 1.0
        if source_id in self.edges and target_id in self.edges[source_id]:
            return self.edges[source_id][target_id]["trust"]
        
        # Simple recursive step for depth 2
        if max_depth > 0:
            total_trust = 0.0
            count = 0
            if source_id in self.edges:
                for intermediary_id, rel in self.edges[source_id].items():
                    if rel["trust"] > 0.5: # Only trust trusted sources
                        i_trust = self._calculate_multi_hop_trust(intermediary_id, target_id, max_depth - 1)
                        total_trust += rel["trust"] * i_trust
                        count += 1
            if count > 0:
                return total_trust / count
        return 0.0

    def _ensure_edge(self, actor_id: str, target_id: str):
        if actor_id not in self.edges:
            self.edges[actor_id] = {}
        if target_id not in self.edges[actor_id]:
            self.edges[actor_id][target_id] = {
                "trust": 0.0,
                "affinity": 0.0,
                "debt": 0.0,
                "interactions": 0
            }

    async def _maintain_memory(self):
        for actor_id in self.edges:
            for target_id, rel in self.edges[actor_id].items():
                rel["debt"] *= 0.99
                rel["trust"] *= 0.999
                rel["affinity"] *= 0.999
