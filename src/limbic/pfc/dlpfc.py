import asyncio
import time
import logging
import uuid
import random
import json
from typing import List, Dict, Any
import grpc
from limbic.bus import LimbicBus
from limbic.generated import limbic_pb2, limbic_pb2_grpc

logger = logging.getLogger(__name__)

class DLPFC:
    """
    Dorsolateral Prefrontal Cortex: Responsible for planning, executive control, 
    and maintaining working memory via gRPC.
    """
    def __init__(self, bus: LimbicBus, wm_address: str = "localhost:50051"):
        self.bus = bus
        self.wm_address = wm_address
        self.iterations = 10
        self.pending_strategies = {} # planning_id -> {action: strategy}
        
        self.bus.subscribe("STIMULUS", self.on_stimulus)
        self.bus.subscribe("CONTEXT_RECALLED", self.on_context_recalled)
        self.bus.subscribe("CONFLICT_DETECTED", self.on_conflict)
        self.bus.subscribe("EFFORT_REQUIRED", self.on_effort_required)
        self.bus.subscribe("ACTION_RESULT", self.on_action_result)
        self.bus.subscribe("ACTION_COMMAND", self.on_action_command)

    async def _get_wm_stub(self):
        # We use the same address as the daemon's gRPC server
        channel = grpc.aio.insecure_channel(self.wm_address)
        return limbic_pb2_grpc.WorkingMemoryServiceStub(channel)

    async def add_to_working_memory(self, key: str, value: str, importance: float = 1.0):
        try:
            stub = await self._get_wm_stub()
            await stub.SetItem(limbic_pb2.WorkingMemoryItem(
                key=key,
                value=value,
                decay=0.1 / max(0.1, importance)
            ))
        except Exception as e:
            logger.debug(f"DLPFC: Working memory update skipped (expected during startup): {e}")

    async def get_working_memory(self) -> List[limbic_pb2.WorkingMemoryItem]:
        try:
            stub = await self._get_wm_stub()
            response = await stub.GetItems(limbic_pb2.Empty())
            return response.items
        except Exception as e:
            logger.debug(f"DLPFC: Working memory query skipped: {e}")
            return []

    async def on_stimulus(self, stimulus):
        content = getattr(stimulus, 'content', str(stimulus))
        await self.add_to_working_memory(f"stimulus_{int(time.time())}", content, importance=0.8)
        await self.replan()

    async def on_context_recalled(self, contexts):
        for i, ctx in enumerate(contexts):
            await self.add_to_working_memory(f"context_{i}_{int(time.time())}", str(ctx), importance=0.5)
        await self.replan()

    async def on_conflict(self, conflict_data):
        logger.info(f"DLPFC: Conflict detected, increasing effort. {conflict_data}")
        await self.replan(iterations=self.iterations * 2)

    async def on_effort_required(self, effort_data):
        level = effort_data.get("level", 0.5)
        logger.info(f"DLPFC: High effort signaled ({level}), increasing iterations.")
        self.iterations = min(50, int(self.iterations * (1 + level)))

    async def on_action_command(self, command):
        if command.get("source") == "PFC":
            pid = command.get("id")
            action = command.get("action")
            if pid in self.pending_strategies and action in self.pending_strategies[pid]:
                strategy = self.pending_strategies[pid][action]
                logger.info(f"DLPFC: Action command received for {action}. Storing strategy: {strategy}")
                await self.add_to_working_memory("active_strategy", json.dumps(strategy), importance=0.9)
            
            # Clean up old pending strategies
            if len(self.pending_strategies) > 50:
                self.pending_strategies.clear()

    async def on_action_result(self, result):
        action = result.get("action")
        success = result.get("success", True)
        logger.info(f"DLPFC: Action {action} result: {'success' if success else 'failure'}")
        
        if success:
            # Check for next step in active strategy
            wm_items = await self.get_working_memory()
            strategy_item = next((item for item in wm_items if item.key == "active_strategy"), None)
            if strategy_item:
                try:
                    strategy = json.loads(strategy_item.value)
                    if strategy and strategy[0] == action:
                        next_steps = strategy[1:]
                        if next_steps:
                            next_action = next_steps[0]
                            logger.info(f"DLPFC: Strategy progression. Next: {next_action}")
                            await self.add_to_working_memory("active_strategy", json.dumps(next_steps), importance=0.9)
                            
                            planning_id = str(uuid.uuid4())
                            plan = {
                                "id": planning_id,
                                "action": next_action,
                                "probability": 1.0,
                                "context": [item.value for item in wm_items]
                            }
                            await self.bus.publish("CANDIDATE_PLAN", plan)
                        else:
                            logger.info("DLPFC: Strategy completed.")
                            await self.add_to_working_memory("active_strategy", "[]", importance=0.1)
                except Exception as e:
                    logger.error(f"DLPFC: Error processing strategy: {e}")

    async def replan(self, iterations=None):
        if iterations is None:
            iterations = self.iterations

        wm_items = await self.get_working_memory()
        current_context = [item.value for item in wm_items]
        
        if not current_context:
            current_context = ["idle"]

        planning_id = str(uuid.uuid4())
        logger.info(f"DLPFC: Strategic planning ({planning_id}) with context: {current_context}")
        
        # Probabilistic sampling of potential actions
        potential_actions = ["OBSERVE", "EXPLORE", "DEFEND", "COOPERATE", "RETREAT", "STAY"]
        
        # Heuristics based on context
        context_str = " ".join(current_context).lower()
        weights = {action: 1.0 for action in potential_actions}
        
        if any(word in context_str for word in ["threat", "fear", "danger", "enemy"]):
            weights["DEFEND"] += 5.0
            weights["RETREAT"] += 3.0
        if any(word in context_str for word in ["reward", "food", "goal", "interesting"]):
            weights["EXPLORE"] += 4.0
            weights["COOPERATE"] += 2.0
        if any(word in context_str for word in ["social", "friend", "ally", "other"]):
            weights["COOPERATE"] += 5.0

        # Sample multiple candidate plans
        num_candidates = max(2, min(5, iterations // 2))
        self.pending_strategies[planning_id] = {}
        
        for _ in range(num_candidates):
            first_action = random.choices(potential_actions, weights=list(weights.values()), k=1)[0]
            strategy = [first_action]
            
            # Simple heuristic for next steps (strategic planning)
            if first_action == "OBSERVE":
                strategy.extend(random.choices(["EXPLORE", "COOPERATE"], k=1))
            elif first_action == "EXPLORE":
                strategy.extend(random.choices(["OBSERVE", "STAY"], k=1))
            elif first_action == "DEFEND":
                strategy.extend(["RETREAT"])
            elif first_action == "COOPERATE":
                strategy.extend(random.choices(["COOPERATE", "STAY"], k=1))
            
            self.pending_strategies[planning_id][first_action] = strategy
            
            plan = {
                "id": planning_id,
                "action": first_action,
                "probability": weights[first_action] / sum(weights.values()),
                "context": current_context
            }
            await self.bus.publish("CANDIDATE_PLAN", plan)

    async def run(self):
        while True:
            # Maintain planning cycle or check for drift
            await asyncio.sleep(10)
