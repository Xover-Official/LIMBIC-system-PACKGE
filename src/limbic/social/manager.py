import asyncio
import logging
from typing import List, Optional
from limbic.bus import LimbicBus
from limbic.persistence.sqlite_manager import SQLiteManager
from limbic.social.tpj import TPJ
from limbic.social.mirror_neurons import MirrorNeuronSystem
from limbic.social.memory import SocialMemory
from limbic.social.norms import CulturalNorms
from limbic.social.reputation import ReputationManagement

logger = logging.getLogger(__name__)

class SocialCognitionManager:
    """
    Unifies the Social Cognition components:
    - TPJ (Theory of Mind)
    - Mirror Neuron System (Empathy)
    - Social Memory (Trust/Debt)
    - Cultural Norms (Conformity)
    - Reputation Management (Social Self)
    """
    def __init__(self, bus: LimbicBus, sql_manager: Optional[SQLiteManager] = None, pg_manager: Optional[Any] = None):
        self.bus = bus
        self.tpj = TPJ(bus)
        self.mirror_neurons = MirrorNeuronSystem(bus)
        self.memory = SocialMemory(bus, sql_manager, pg_manager)
        self.norms = CulturalNorms(bus)
        self.reputation = ReputationManagement(bus)
        
        self.components = [
            self.tpj,
            self.mirror_neurons,
            self.memory,
            self.norms,
            self.reputation
        ]

    async def run(self):
        logger.info("SocialCognitionManager starting...")
        
        # Start all sub-components
        tasks = [asyncio.create_task(component.run()) for component in self.components]
        
        # Phase 3: Communication Loop implementation
        asyncio.create_task(self.communication_loop())
        
        # Monitor components
        while True:
            # Aggregate social state and publish to LimbicBus
            social_state = {
                "reputation": self.reputation.reputation,
                "global_trust": self._calculate_global_trust(),
                "norm_complexity": len(self.norms.context_norms),
                "active_connections": 5, # Mocked for FactoryOS
                "signal_strength": 0.85, # Mocked for FactoryOS
                "traffic_rate": 12.4 # Mocked for FactoryOS (kb/s)
            }
            await self.bus.publish("SOCIAL_STATE_SUMMARY", social_state)
            
            # Publish to GWT (Global Workspace Theory)
            await self.bus.publish("SOCIAL_SIGNAL", {
                "salience": 0.6, # Base salience for social signals
                "content": social_state,
                "origin": "social_cognition_manager"
            })
            
            await asyncio.sleep(2)

    async def communication_loop(self):
        """Phase 3: Communication Loop implementation"""
        while True:
            # Simulate an incoming message
            await asyncio.sleep(15)
            ping_data = {
                "sender": "FACTORY_CORE_ALPHA",
                "message": "Status check requested.",
                "signal_strength": 0.92
            }
            await self.bus.publish("COMMUNICATION_INCOMING", ping_data)
            logger.info(f"Incoming communication from {ping_data['sender']}")
            
            # Auto-respond
            await asyncio.sleep(2)
            await self.bus.publish("COMMUNICATION_OUTGOING", {
                "recipient": "FACTORY_CORE_ALPHA",
                "message": "Status OK. Heartbeat active.",
                "status": "DELIVERED"
            })

    def _calculate_global_trust(self) -> float:
        if not self.memory.edges.get("self"):
            return 0.5
        
        trusts = [rel["trust"] for rel in self.memory.edges["self"].values()]
        return sum(trusts) / len(trusts) if trusts else 0.5
