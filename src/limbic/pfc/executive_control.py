import asyncio
import logging
from typing import Dict, List
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class ExecutiveControl:
    """
    Final decision layer that arbitrates between candidate plans
    and can override limbic impulses.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.cycle_results: Dict[str, List[dict]] = {} # planning_id -> list of valued plans
        
        self.bus.subscribe("UTILITY_ASSIGNED", self.on_utility_assigned)
        self.bus.subscribe("PLAN_VETTED", self.on_plan_vetted)

    async def on_utility_assigned(self, data):
        pid = data.get("id")
        if not pid: return
        
        if pid not in self.cycle_results:
            self.cycle_results[pid] = []
        
        self.cycle_results[pid].append(data)
        
        # Arbitrate after a short window to collect multiple candidates
        await asyncio.sleep(0.2) 
        await self.arbitrate(pid)

    async def on_plan_vetted(self, vetting):
        # Immediate veto for severe moral/social violations
        if not vetting.get("approved") and vetting.get("score", 0) < -0.3:
            pid = vetting.get("id")
            action = vetting.get("plan", {}).get("action")
            logger.warning(f"ExecutiveControl: VETOING action {action} due to social constraint violation")
            # Immediate override signal to inhibit the drive that might be pushing this
            await self.bus.publish("LIMBIC_OVERRIDE", {
                "suppress": ["SEEKING", "PANIC", "FEAR"], 
                "reason": f"MORAL_VETO_{action}"
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
        
        if utility > 0.4:
            logger.info(f"ExecutiveControl: PFC Decision: {action} (utility: {utility:.2f})")
            await self.bus.publish("ACTION_COMMAND", {"action": action, "source": "PFC", "id": pid})
            
            # Send Top-Down Override signals to subcortical engines
            if utility > 0.8:
                # Total dominance
                await self.bus.publish("LIMBIC_OVERRIDE", {
                    "suppress": ["FEAR", "PANIC", "CARE", "SEEKING"],
                    "reason": "EXECUTIVE_DOMINANCE"
                })
            elif action == "DEFEND":
                await self.bus.publish("LIMBIC_OVERRIDE", {
                    "suppress": ["SEEKING", "CARE"],
                    "reason": "PRIORITIZE_DEFENSE"
                })
            elif action == "COOPERATE":
                await self.bus.publish("LIMBIC_OVERRIDE", {
                    "suppress": ["FEAR"],
                    "reason": "OVERRIDE_FEAR_FOR_COOPERATION"
                })
        else:
            logger.info(f"ExecutiveControl: Cycle {pid} - Low utility ({utility:.2f}), no PFC override.")

    async def run(self):
        while True:
            await asyncio.sleep(1)
            # Periodic cleanup of leaked cycle results
            if len(self.cycle_results) > 100:
                self.cycle_results.clear()
