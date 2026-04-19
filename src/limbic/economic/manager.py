import asyncio
import logging
import json
from typing import Dict, Any
from limbic.bus import LimbicBus
from limbic.economic.wallet import Wallet

logger = logging.getLogger(__name__)

class EconomicEngine:
    def __init__(self, bus: LimbicBus, wallet: Wallet, initial_balance: float = 100.0):
        self.bus = bus
        self.wallet = wallet
        self.balance = initial_balance
        self.total_spent = 0.0
        self.cost_per_token = 0.00001
        self.cost_per_action = 0.01

    async def run(self):
        logger.info("Economic Engine starting...")
        self.bus.subscribe("ACTION_COMMAND", self.charge_for_action)
        self.bus.subscribe("WORKSPACE_BROADCAST", self.charge_for_thought)
        
        while True:
            # Report economic state
            await self.bus.publish("ECONOMIC_STATE", {
                "balance": self.balance,
                "total_spent": self.total_spent,
                "wallet_address": self.wallet.address
            })
            
            # Map low balance to FINANCIAL_HUNGER drive
            # If balance is 0, hunger is 1.0. If balance is 100+, hunger is 0.0
            financial_hunger = max(0.0, min(1.0, 1.0 - (self.balance / 100.0)))
            
            # Publish as a stimulus to be picked up by Hypothalamus
            # We use a special topic or generic STIMULUS
            await self.bus.publish("STIMULUS", {
                "source": "economic_engine",
                "metadata": {"financial_hunger": financial_hunger}
            })
            
            await asyncio.sleep(60)

    async def charge_for_action(self, data: Dict[str, Any]):
        self.balance -= self.cost_per_action
        self.total_spent += self.cost_per_action
        logger.debug(f"Charged {self.cost_per_action} for action. New balance: {self.balance}")

    async def charge_for_thought(self, data: Dict[str, Any]):
        # Mocking token counting: roughly 4 chars per token
        content = data.get("content", "")
        if isinstance(content, dict):
            content = json.dumps(content)
        tokens = len(str(content)) / 4 
        cost = tokens * self.cost_per_token
        self.balance -= cost
        self.total_spent += cost
        logger.debug(f"Charged {cost:.6f} for thought. New balance: {self.balance:.6f}")
