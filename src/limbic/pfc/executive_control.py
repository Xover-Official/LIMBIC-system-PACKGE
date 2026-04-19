import asyncio
import logging
from typing import Dict, List
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class ExecutiveControl:
    """
    Final decision layer that arbitrates between candidate plans.
    Implements deliberative delay and dynamic decision thresholds.
    Can override limbic impulses with targeted suppression.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.cycle_results: Dict[str, List[dict]] = {} # planning_id -> list of valued plans
        self.effort_level = 0.0
        self.base_deliberation_window = 0.2
        
        self.bus.subscribe("UTILITY_ASSIGNED", self.on_utility_assigned)
        self.bus.subscribe("PLAN_VETTED", self.on_plan_vetted)
        self.bus.subscribe("EFFORT_REQUIRED", self.on_effort_required)

    async def on_effort_required(self, data):
        self.effort_level = data.get("level", 0.0)

    async def on_utility_assigned(self, data):
        pid = data.get("id")
        if not pid: return
        
        if pid not in self.cycle_results:
            self.cycle_results[pid] = []
        
        self.cycle_results[pid].append(data)
        
        # Deliberative Delay: wait longer if ACC signals high effort
        # This allows more time for all PFC regions to process candidates
        window = self.base_deliberation_window + (self.effort_level * 0.8)
        
        await asyncio.sleep(window) 
        await self.arbitrate(pid)

    async def on_plan_vetted(self, vetting):
        # Immediate veto for severe moral/social violations
        if not vetting.get("approved") and vetting.get("score", 0) < -0.5:
            pid = vetting.get("id")
            action = vetting.get("plan", {}).get("action")
            logger.warning(f"ExecutiveControl: URGENT VETO for {action} due to social constraint")
            
            # Immediate override signal to inhibit impulsive drives
            await self.bus.publish("LIMBIC_OVERRIDE", {
                "suppress": ["SEEKING", "PANIC", "FEAR", "RAGE"], 
                "reason": f"URGENT_MORAL_VETO_{action}"
            })

    async def arbitrate(self, pid):
        if pid not in self.cycle_results: return
        
        results = self.cycle_results[pid]
        if not results: return
        
        # Sort candidates by utility
        sorted_results = sorted(results, key=lambda x: x["utility"], reverse=True)
        best = sorted_results[0]
        
        # Prevent double arbitration for the same cycle
        del self.cycle_results[pid]
        
        action = best["plan"]["action"]
        utility = best["utility"]
        
        # Dynamic Decision Threshold: Require higher utility when effort is high
        # (Implementing impulse control and caution)
        threshold = 0.3 + (self.effort_level * 0.3)
        
        if utility > threshold:
            logger.info(f"ExecutiveControl: PFC Decision: {action} (utility: {utility:.2f}, threshold: {threshold:.2f})")
            await self.bus.publish("ACTION_COMMAND", {"action": action, "source": "PFC", "id": pid})
            
            # Targeted Top-Down Override signals to subcortical engines
            to_suppress = []
            if action == "COOPERATE":
                to_suppress = ["FEAR", "RAGE"]
            elif action == "EXPLORE":
                to_suppress = ["FEAR", "PANIC"]
            elif action == "DEFEND":
                to_suppress = ["CARE", "SEEKING"]
            elif action == "RETREAT":
                to_suppress = ["SEEKING"]
            elif action == "STAY":
                to_suppress = ["SEEKING", "PANIC", "FEAR"]
                
            if to_suppress:
                await self.bus.publish("LIMBIC_OVERRIDE", {
                    "suppress": to_suppress,
                    "reason": f"STRATEGIC_OVERRIDE_{action}",
                    "level": 0.5 + (utility * 0.3)
                })
        else:
            logger.info(f"ExecutiveControl: Cycle {pid} - Best utility {utility:.2f} below threshold {threshold:.2f}. Deferred.")

    async def run(self):
        while True:
            await asyncio.sleep(1)
            # Periodic cleanup
            if len(self.cycle_results) > 100:
                self.cycle_results.clear()
