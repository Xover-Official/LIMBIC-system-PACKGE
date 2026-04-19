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
        self.total_earned = 0.0
        self.cost_per_token = 0.00001
        self.cost_per_action = 0.01
        self.base_income = 0.5  # Salary loop income
        self.income_interval = 10 # seconds

    async def run(self):
        logger.info("Economic Engine starting...")
        self.bus.subscribe("ACTION_COMMAND", self.charge_for_action)
        self.bus.subscribe("WORKSPACE_BROADCAST", self.charge_for_thought)
        
        # Start salary loop
        asyncio.create_task(self.salary_loop())
        
        while True:
            # Report economic state
            await self.bus.publish("ECONOMIC_STATE", {
                "balance": self.balance,
                "total_spent": self.total_spent,
                "total_earned": self.total_earned,
                "wallet_address": self.wallet.address,
                "burn_rate": self.total_spent / max(1, self.total_spent + self.total_earned), # Simplified burn rate
                "wealth_velocity": self.total_earned - self.total_spent
            })
            
            # Map low balance to FINANCIAL_HUNGER drive
            financial_hunger = max(0.0, min(1.0, 1.0 - (self.balance / 100.0)))
            
            await self.bus.publish("STIMULUS", {
                "source": "economic_engine",
                "metadata": {"financial_hunger": financial_hunger}
            })
            
            await asyncio.sleep(5) # Increased frequency for UI updates

    async def salary_loop(self):
        """Phase 1: Salary Loop implementation"""
        while True:
            await asyncio.sleep(self.income_interval)
            self.balance += self.base_income
            self.total_earned += self.base_income
            logger.info(f"Salary credited: {self.base_income}. New balance: {self.balance}")
            await self.bus.publish("INCOME_EVENT", {"amount": self.base_income, "source": "salary_loop"})

    async def charge_for_action(self, data: Dict[str, Any]):
        """Phase 2: Expense Loop - Action charges"""
        self.balance -= self.cost_per_action
        self.total_spent += self.cost_per_action
        logger.debug(f"Charged {self.cost_per_action} for action. New balance: {self.balance}")
        await self.bus.publish("EXPENSE_EVENT", {"amount": self.cost_per_action, "type": "action"})

    async def charge_for_thought(self, data: Dict[str, Any]):
        """Phase 2: Expense Loop - Thought charges"""
        # Mocking token counting: roughly 4 chars per token
        content = data.get("content", "")
        if isinstance(content, dict):
            content = json.dumps(content)
        tokens = len(str(content)) / 4 
        cost = tokens * self.cost_per_token
        self.balance -= cost
        self.total_spent += cost
        logger.debug(f"Charged {cost:.6f} for thought. New balance: {self.balance:.6f}")
        await self.bus.publish("EXPENSE_EVENT", {"amount": cost, "type": "thought"})
