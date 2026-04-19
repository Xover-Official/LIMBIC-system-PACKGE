import asyncio
import logging
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class ACC:
    """
    Anterior Cingulate Cortex: Conflict monitor and effort allocator.
    Detects Plan-Limbic and Plan-Plan conflicts to signal required cognitive effort.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.current_emotions = {}
        self.candidate_plans = {} # planning_id -> list of plans
        
        self.bus.subscribe("ENGINE_ACTIVE", self.on_engine_active)
        self.bus.subscribe("CANDIDATE_PLAN", self.on_candidate_plan)
        self.bus.subscribe("UTILITY_ASSIGNED", self.on_utility_assigned)

    async def on_engine_active(self, engine_info):
        self.current_emotions[engine_info["name"]] = engine_info["level"]
        await self.check_limb_plan_conflict()

    async def on_candidate_plan(self, plan):
        pid = plan["id"]
        if pid not in self.candidate_plans:
            self.candidate_plans[pid] = []
        self.candidate_plans[pid].append(plan)
        
        if len(self.candidate_plans[pid]) > 1:
            await self.check_plan_plan_conflict(pid)

    async def on_utility_assigned(self, data):
        # We monitor if utilities are very close (high choice difficulty)
        pass

    async def check_limb_plan_conflict(self):
        # Detect conflict between subcortical drive and cortical plan
        fear_level = self.current_emotions.get("FEAR", 0.0)
        seeking_level = self.current_emotions.get("SEEKING", 0.0)
        
        for pid, plans in self.candidate_plans.items():
            for plan in plans:
                action = plan["action"]
                conflict_level = 0.0
                if action == "EXPLORE" and fear_level > 0.6:
                    conflict_level = (fear_level + 0.5) / 2
                elif action == "DEFEND" and seeking_level > 0.8:
                    conflict_level = (seeking_level + 0.2) / 2
                elif action == "RETREAT" and seeking_level > 0.9:
                    conflict_level = 0.7
                    
                if conflict_level > 0.5:
                    logger.warning(f"ACC: Plan-Limbic conflict detected for {action}: {conflict_level:.2f}")
                    await self.bus.publish("CONFLICT_DETECTED", {"id": pid, "action": action, "level": conflict_level})
                    await self.bus.publish("EFFORT_REQUIRED", {"level": conflict_level})

    async def check_plan_plan_conflict(self, pid):
        plans = self.candidate_plans[pid]
        if len(plans) < 2: return
        
        # If we have multiple candidates with similar probabilities, it's a conflict
        probs = [p.get("probability", 0.0) for p in plans]
        if max(probs) < 0.4 and len(probs) > 2:
            logger.info(f"ACC: Plan-Plan conflict detected (choice difficulty)")
            await self.bus.publish("EFFORT_REQUIRED", {"level": 0.6})

    async def run(self):
        while True:
            # Cleanup old candidate tracking
            await asyncio.sleep(60)
            self.candidate_plans.clear()
            self.current_emotions.clear()
