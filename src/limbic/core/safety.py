import asyncio
import logging
from typing import Dict, Any, List
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class RedFlagSafetySystem:
    """
    Phase 3: Red Flag Safety System
    Monitors system state for critical risks and triggers alerts.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.threat_level = "GREEN"
        self.risk_factors = []
        self.system_integrity = 1.0
        self.last_economic_state = {}
        self.last_limbic_state = {}

    async def run(self):
        logger.info("Red Flag Safety System starting...")
        self.bus.subscribe("ECONOMIC_STATE", self.monitor_economics)
        self.bus.subscribe("LIMBIC_STATE", self.monitor_limbic)
        
        while True:
            await self.evaluate_risks()
            
            await self.bus.publish("SAFETY_STATE", {
                "threat_level": self.threat_level,
                "risk_factors": self.risk_factors,
                "system_integrity": self.system_integrity,
                "override_status": "AUTOMATED"
            })
            
            await asyncio.sleep(2)

    async def monitor_economics(self, data: Dict[str, Any]):
        self.last_economic_state = data

    async def monitor_limbic(self, data: Dict[str, Any]):
        self.last_limbic_state = data

    async def evaluate_risks(self):
        new_risks = []
        
        # Check Balance
        balance = self.last_economic_state.get("balance", 100.0)
        if balance < 10.0:
            new_risks.append("CRITICAL_LOW_BALANCE")
        elif balance < 50.0:
            new_risks.append("WARNING_LOW_BALANCE")
            
        # Check Arousal/Stress
        arousal = self.last_limbic_state.get("arousal", 0.0)
        if arousal > 0.9:
            new_risks.append("SYSTEMIC_STRESS_EXCEEDED")
        elif arousal > 0.7:
            new_risks.append("HIGH_AROUSAL_WARNING")
            
        # Determine Threat Level
        if any("CRITICAL" in r or "EXCEEDED" in r for r in new_risks):
            self.threat_level = "RED"
            self.system_integrity = max(0.2, self.system_integrity - 0.05)
        elif any("WARNING" in r or "HIGH" in r for r in new_risks):
            self.threat_level = "AMBER"
            self.system_integrity = min(1.0, self.system_integrity + 0.01) # Recovery
        else:
            self.threat_level = "GREEN"
            self.system_integrity = min(1.0, self.system_integrity + 0.05) # Full Recovery
            
        self.risk_factors = new_risks
        
        if self.threat_level == "RED":
            await self.bus.publish("RED_FLAG_ALERT", {"threats": self.risk_factors})
