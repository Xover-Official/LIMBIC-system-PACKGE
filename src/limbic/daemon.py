import asyncio
import logging
import grpc
import time
from concurrent import futures
from limbic.bus import LimbicBus
from limbic.generated import limbic_pb2_grpc, limbic_pb2
from limbic.core.hypothalamus import Hypothalamus
from limbic.core.amygdala import Amygdala
from limbic.core.hippocampus import HippocampusV2
from limbic.core.nucleus_accumbens import NucleusAccumbens
from limbic.core.insula import Insula
from limbic.persistence.sqlite_manager import SQLiteManager, EventLogger
from limbic.persistence.vector_store import VectorStore
from limbic.engines.seeking import SeekingEngine
from limbic.engines.fear import FearEngine
from limbic.engines.panic import PanicEngine
from limbic.engines.care import CareEngine

# PFC Imports
from limbic.pfc.dlpfc import DLPFC
from limbic.pfc.vmpfc import VMPFC
from limbic.pfc.ofc import OFC
from limbic.pfc.acc import ACC
from limbic.pfc.executive_control import ExecutiveControl

# Sensorimotor Imports
try:
    from sensorimotor.registry import ToolRegistry
    from sensorimotor.subcortical.cerebellum import Cerebellum
    from sensorimotor.subcortical.basal_ganglia import BasalGanglia
    from sensorimotor.cortex.sensory import SensoryCortex
    from sensorimotor.cortex.motor import MotorCortex
    SENSORIMOTOR_AVAILABLE = True
except ImportError:
    logger.warning("sensorimotor-system package not found. Sensorimotor features will be disabled.")
    SENSORIMOTOR_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LimbicServicer(limbic_pb2_grpc.LimbicServiceServicer):
    def __init__(self, bus: LimbicBus, daemon: 'LimbicDaemon'):
        self.bus = bus
        self.daemon = daemon

    async def InjectStimulus(self, request, context):
        logger.info(f"Received stimulus from {request.source}")
        await self.bus.publish("STIMULUS", request)
        return limbic_pb2.LimbicResponse(accepted=True, message="Stimulus received")

    async def GetLimbicState(self, request, context):
        return self.daemon.get_current_state()

    async def StreamState(self, request, context):
        last_timestamp = 0
        while True:
            state = self.daemon.get_current_state()
            if state.timestamp > last_timestamp:
                yield state
                last_timestamp = state.timestamp
            await asyncio.sleep(1)

    async def GetPlans(self, request, context):
        plans = []
        # Get current plans from DLPFC/Executive
        # For simplicity, we'll store them in the daemon or query components
        for action, data in self.daemon.active_plans.items():
            plans.append(limbic_pb2.Plan(
                action=action,
                confidence=data.get("confidence", 0.0),
                utility=data.get("utility", 0.0),
                approved=data.get("approved", False),
                status=data.get("status", "PENDING")
            ))
        return limbic_pb2.PlanList(plans=plans)

class LimbicDaemon:
    def __init__(self, port=50051):
        self.port = port
        self.bus = LimbicBus()
        self.servicer = LimbicServicer(self.bus, self)
        
        # Core
        self.hypothalamus = Hypothalamus(self.bus)
        self.amygdala = Amygdala(self.bus)
        self.vs = VectorStore()
        self.hippocampus = HippocampusV2(self.bus, self.vs)
        self.na = NucleusAccumbens(self.bus)
        self.insula = Insula(self.bus)
        
        # PFC
        self.dlpfc = DLPFC(self.bus)
        self.vmpfc = VMPFC(self.bus)
        self.ofc = OFC(self.bus)
        self.acc = ACC(self.bus)
        self.executive = ExecutiveControl(self.bus)
        
        # Persistence
        self.sql_manager = SQLiteManager()
        self.event_logger = EventLogger(self.bus, self.sql_manager)
        
        # Engines
        self.engines = {
            "SEEKING": SeekingEngine(self.bus),
            "FEAR": FearEngine(self.bus),
            "PANIC": PanicEngine(self.bus),
            "CARE": CareEngine(self.bus)
        }

        # Sensorimotor Integration
        if SENSORIMOTOR_AVAILABLE:
            self.tool_registry = ToolRegistry()
            self.cerebellum = Cerebellum()
            self.basal_ganglia = BasalGanglia(self.bus)
            self.sensory_cortex = SensoryCortex(self.bus, self.cerebellum)
            self.motor_cortex = MotorCortex(self.bus, self.tool_registry, self.cerebellum)
            
            # Register basic tools
            self.tool_registry.register_tool("move", "Move the agent", lambda x=0, y=0: f"Moved to {x}, {y}")
            self.tool_registry.register_tool("grasp", "Grasp an object", lambda item="nothing": f"Grasped {item}")
        
        # Current Global State
        self.arousal = 0.5
        self.valence = 0.0
        self.current_drives = {}
        self.active_engines = {}
        self.active_plans = {}
        
        # Subscribe to updates for global state
        self.bus.subscribe("DRIVE_UPDATE", self.update_drives)
        self.bus.subscribe("ENGINE_ACTIVE", self.update_engines)
        self.bus.subscribe("SIGNIFICANCE_EVALUATED", self.update_valence_arousal)
        
        # Subscribe to PFC events
        self.bus.subscribe("PLAN_GENERATED", self.on_plan_generated)
        self.bus.subscribe("PLAN_VETTED", self.on_plan_vetted)
        self.bus.subscribe("UTILITY_ASSIGNED", self.on_utility_assigned)
        self.bus.subscribe("ACTION_COMMAND", self.on_action_command)
        self.bus.subscribe("ACTION_RESULT", self.on_action_result)
        self.bus.subscribe("ACTION_FAILURE", self.on_action_failure)

    def update_drives(self, drives):
        self.current_drives = drives

    def update_engines(self, engine_info):
        self.active_engines[engine_info["name"]] = engine_info["level"]

    def update_valence_arousal(self, eval):
        self.valence = (self.valence * 0.7) + (eval["valence"] * 0.3)
        self.arousal = (self.arousal * 0.7) + (eval["arousal"] * 0.3)

    def on_plan_generated(self, plan):
        action = plan["action"]
        self.active_plans[action] = {
            "confidence": plan.get("confidence", 0.0),
            "status": "GENERATED"
        }

    def on_plan_vetted(self, vetting):
        action = vetting["plan"]["action"]
        if action in self.active_plans:
            self.active_plans[action]["approved"] = vetting["approved"]
            self.active_plans[action]["status"] = "VETTED" if vetting["approved"] else "BLOCKED"

    def on_utility_assigned(self, data):
        action = data["plan"]["action"]
        if action in self.active_plans:
            self.active_plans[action]["utility"] = data["utility"]
            self.active_plans[action]["status"] = "VALUED"

    def on_action_command(self, command):
        action = command["action"]
        if action in self.active_plans:
            self.active_plans[action]["status"] = "EXECUTING"

    def on_action_result(self, result):
        action = result["action"]
        if action in self.active_plans:
            self.active_plans[action]["status"] = "COMPLETED"
            self.active_plans[action]["result"] = result["result"]

    def on_action_failure(self, failure):
        action = failure["action"]
        if action in self.active_plans:
            self.active_plans[action]["status"] = "FAILED"
            self.active_plans[action]["error"] = failure["error"]

    def get_current_state(self):
        dominant = "CALM"
        if self.active_engines:
            dominant = max(self.active_engines, key=self.active_engines.get)
            
        return limbic_pb2.LimbicState(
            arousal=self.arousal,
            valence=self.valence,
            drives=self.current_drives,
            emotions=self.active_engines,
            dominant_engine=dominant,
            timestamp=int(time.time())
        )

    async def run(self):
        await self.sql_manager.init_db()
        
        server = grpc.aio.server()
        limbic_pb2_grpc.add_LimbicServiceServicer_to_server(self.servicer, server)
        listen_addr = f'[::]:{self.port}'
        server.add_insecure_port(listen_addr)
        
        logger.info(f"Starting gRPC server on {listen_addr}")
        await server.start()
        
        # Run all components
        tasks = [
            asyncio.create_task(self.bus.run()),
            asyncio.create_task(self.hypothalamus.run()),
            asyncio.create_task(self.hippocampus.run()),
            asyncio.create_task(self.dlpfc.run()),
            asyncio.create_task(self.vmpfc.run()),
            asyncio.create_task(self.ofc.run()),
            asyncio.create_task(self.acc.run()),
            asyncio.create_task(self.executive.run()),
            asyncio.create_task(self.engines["SEEKING"].run()),
            asyncio.create_task(self.engines["FEAR"].run()),
            asyncio.create_task(self.engines["PANIC"].run()),
            asyncio.create_task(self.engines["CARE"].run()),
        ]

        if SENSORIMOTOR_AVAILABLE:
            for component in [self.sensory_cortex, self.motor_cortex, self.basal_ganglia]:
                if hasattr(component, "run") and asyncio.iscoroutinefunction(component.run):
                    tasks.append(asyncio.create_task(component.run()))
        
        try:
            await server.wait_for_termination()
        except asyncio.CancelledError:
            for t in tasks: t.cancel()
            await server.stop(0)

if __name__ == "__main__":
    daemon = LimbicDaemon()
    try:
        asyncio.run(daemon.run())
    except KeyboardInterrupt:
        pass
