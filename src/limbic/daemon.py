import asyncio
import logging
import grpc
import time
import os
import uuid
import json
from concurrent import futures
from typing import Dict, Any, List

from limbic.bus import LimbicBus
from limbic.generated import limbic_pb2_grpc, limbic_pb2
from limbic.core.hypothalamus import Hypothalamus
from limbic.core.amygdala import Amygdala
from limbic.core.hippocampus import HippocampusV2
from limbic.core.nucleus_accumbens import NucleusAccumbens
from limbic.core.insula import Insula
from limbic.persistence.sqlite_manager import SQLiteManager, EventLogger
from limbic.persistence.vector_store import VectorStore
from limbic.persistence.postgres_manager import PostgresManager
from limbic.engines.seeking import SeekingEngine
from limbic.engines.fear import FearEngine
from limbic.engines.panic import PanicEngine
from limbic.engines.care import CareEngine

# New High-Fidelity Human Analog Imports
from limbic.core.endocrine import EndocrineOrchestrator
from limbic.core.consciousness import ConsciousnessSystemV2
from limbic.core.vagus_nerve import VagusNerve
from limbic.core.pineal_gland import PinealGland
from limbic.core.developmental import AgeLayer
from limbic.linguistic.filters import WernickeFilter, BrocaFilter
from limbic.psychology.lattice import PsychologicalLattice
from limbic.psychology.existential import ExistentialLayer
from limbic.social.genome import SocioculturalGenome
from limbic.social.manager import SocialCognitionManager

# Production-Grade Components
from limbic.pfc.moral_kernel import MoralKernel
from limbic.economic.manager import EconomicEngine
from limbic.economic.wallet import Wallet
from limbic.core.evolution import EvolutionEngine
from limbic.linguistic.registry import SemanticRegistry

# PFC Imports
from limbic.pfc.dlpfc import DLPFC
from limbic.pfc.vmpfc import VMPFC
from limbic.pfc.ofc import OFC
from limbic.pfc.acc import ACC
from limbic.pfc.executive_control import ExecutiveControl
from limbic.pfc.working_memory import WorkingMemoryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Consciousness Imports
try:
    from consciousness.integration import ConsciousnessSystem
    CONSCIOUSNESS_AVAILABLE = True
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "consciousness_system", "src"))
    try:
        from consciousness.integration import ConsciousnessSystem
        CONSCIOUSNESS_AVAILABLE = True
    except ImportError:
        logger.warning("consciousness-system package not found. Consciousness features will be disabled.")
        CONSCIOUSNESS_AVAILABLE = False

class SignedThoughtLogger:
    def __init__(self, bus: LimbicBus, pg_manager: PostgresManager, wallet: Wallet):
        self.bus = bus
        self.pg_manager = pg_manager
        self.wallet = wallet
        self.recent_thoughts: List[Dict[str, Any]] = []
        self.bus.subscribe("WORKSPACE_BROADCAST", self.log_thought)

    async def log_thought(self, data: Dict[str, Any]):
        thought_id = str(uuid.uuid4())
        content = data.get("content", data.get("topic", ""))
        
        # Sign content
        content_str = json.dumps(content) if not isinstance(content, str) else content
        signature = self.wallet.sign_transaction(content_str.encode())
        
        if self.pg_manager:
            await self.pg_manager.add_thought(
                thought_id=thought_id,
                content=content,
                signature=signature,
                signer_id=self.wallet.address
            )
        
        signed_thought = {
            "thought_id": thought_id,
            "content": content_str,
            "signature": signature,
            "signer_id": self.wallet.address
        }
        self.recent_thoughts.append(signed_thought)
        if len(self.recent_thoughts) > 10:
            self.recent_thoughts.pop(0)

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
        
        # Infrastructure
        self.pg_manager = None
        dsn = os.getenv("DATABASE_URL")
        if dsn:
            self.pg_manager = PostgresManager(dsn)
        
        # Security & Identity
        self.wallet = Wallet(os.getenv("WALLET_PRIVATE_KEY"))
        
        # Core
        self.hypothalamus = Hypothalamus(self.bus)
        self.amygdala = Amygdala(self.bus)
        self.vs = VectorStore()
        self.hippocampus = HippocampusV2(self.bus, self.vs)
        self.na = NucleusAccumbens(self.bus)
        self.insula = Insula(self.bus)
        
        # PFC
        self.wm_service = WorkingMemoryService()
        self.dlpfc = DLPFC(self.bus, wm_address=f"localhost:{self.port}")
        self.vmpfc = VMPFC(self.bus)
        self.ofc = OFC(self.bus)
        self.acc = ACC(self.bus)
        self.executive = ExecutiveControl(self.bus)
        
        # Production Components
        self.moral_kernel = MoralKernel(self.bus, os.getenv("AXIOMS_PUBLIC_KEY"))
        self.economic_engine = EconomicEngine(self.bus, self.wallet)
        self.evolution_engine = EvolutionEngine(self.bus)
        self.semantic_registry = SemanticRegistry(self.bus)
        
        # Persistence
        self.sql_manager = SQLiteManager()
        self.event_logger = EventLogger(self.bus, self.sql_manager)
        if self.pg_manager:
            self.thought_logger = SignedThoughtLogger(self.bus, self.pg_manager, self.wallet)
        
        # High-Fidelity Human Analog Systems
        self.endocrine = EndocrineOrchestrator(self.bus)
        self.psych_lattice = PsychologicalLattice(self.bus)
        self.existential_layer = ExistentialLayer(self.bus)
        self.social_genome = SocioculturalGenome(self.bus)
        self.social_cognition = SocialCognitionManager(self.bus, self.sql_manager, self.pg_manager)
        self.consciousness_v2 = ConsciousnessSystemV2(self.bus)
        
        # Project Omega Systems
        self.vagus_nerve = VagusNerve(self.bus)
        self.pineal_gland = PinealGland(self.bus)
        self.wernicke = WernickeFilter(self.bus)
        self.broca = BrocaFilter(self.bus)
        self.age_layer = AgeLayer(self.bus)
        
        # Engines
        self.engines = {
            "SEEKING": SeekingEngine(self.bus),
            "FEAR": FearEngine(self.bus),
            "PANIC": PanicEngine(self.bus),
            "CARE": CareEngine(self.bus)
        }

        # Consciousness
        if CONSCIOUSNESS_AVAILABLE:
            self.consciousness = ConsciousnessSystem(self.bus)
            self.current_focus = ""
            self.focus_salience = 0.0
            self.self_narrative = ""
            self.attention_schema = {}

        # Sensorimotor Integration
        if SENSORIMOTOR_AVAILABLE:
            self.tool_registry = ToolRegistry()
            self.cerebellum = Cerebellum()
            self.basal_ganglia = BasalGanglia(self.bus)
            self.sensory_cortex = SensoryCortex(self.bus, self.cerebellum)
            self.motor_cortex = MotorCortex(self.bus, self.tool_registry, self.cerebellum)
            
            self.tool_registry.register_tool("move", "Move the agent", lambda x=0, y=0: f"Moved to {x}, {y}")
            self.tool_registry.register_tool("grasp", "Grasp an object", lambda item="nothing": f"Grasped {item}")
        
        # Current Global State
        self.arousal = 0.5
        self.valence = 0.0
        self.current_drives = {}
        self.active_engines = {}
        self.active_plans = {}
        self.hormones = {}
        self.phi = 0.0
        self.ego_coherence = 1.0
        self.meaning = 0.5
        self.dread = 0.0
        self.age = 0.0
        self.plasticity = 1.0
        self.vagal_tone = 0.5
        
        # Subscribe to updates for global state
        self.bus.subscribe("DRIVE_UPDATE", self.update_drives)
        self.bus.subscribe("ENGINE_ACTIVE", self.update_engines)
        self.bus.subscribe("SIGNIFICANCE_EVALUATED", self.update_valence_arousal)
        self.bus.subscribe("HORMONE_LEVELS", self.update_hormones)
        self.bus.subscribe("PHI_UPDATE", self.update_phi)
        self.bus.subscribe("PSYCH_STATE", self.update_psych)
        self.bus.subscribe("EXISTENTIAL_STATE", self.update_existential)
        self.bus.subscribe("DEVELOPMENTAL_STATE", self.update_developmental_state)
        self.bus.subscribe("VAGAL_TONE", self.update_vagal_tone)
        
        # Subscribe to PFC events
        self.bus.subscribe("PLAN_GENERATED", self.on_plan_generated)
        self.bus.subscribe("CANDIDATE_PLAN", self.on_plan_generated)
        self.bus.subscribe("PLAN_VETTED", self.on_plan_vetted)
        self.bus.subscribe("UTILITY_ASSIGNED", self.on_utility_assigned)
        self.bus.subscribe("ACTION_COMMAND", self.on_action_command)
        self.bus.subscribe("ACTION_RESULT", self.on_action_result)
        self.bus.subscribe("ACTION_FAILURE", self.on_action_failure)

        if CONSCIOUSNESS_AVAILABLE:
            self.bus.subscribe("WORKSPACE_BROADCAST", self.update_consciousness_focus)
            self.bus.subscribe("SELF_STATE_UPDATE", self.update_self_state)
            self.bus.subscribe("ATTENTION_SCHEMA_UPDATE", self.update_attention_schema)

    def update_consciousness_focus(self, broadcast):
        self.current_focus = broadcast.get("topic", "")
        self.focus_salience = broadcast.get("salience", 0.0)

    def update_self_state(self, state):
        self.self_narrative = state.get("narrative", "")

    def update_attention_schema(self, schema):
        self.attention_schema = schema

    def update_hormones(self, hormones):
        self.hormones = hormones

    def update_phi(self, data):
        self.phi = data.get("phi", 0.0)

    def update_psych(self, state):
        self.ego_coherence = state.get("ego_coherence", 1.0)

    def update_existential(self, state):
        self.meaning = state.get("meaning", 0.5)
        self.dread = state.get("dread", 0.0)

    def update_developmental_state(self, data):
        self.age = data.get("age", 0.0)
        self.plasticity = data.get("plasticity", 1.0)

    def update_vagal_tone(self, data):
        self.vagal_tone = data.get("tone", 0.5)

    def update_drives(self, drives):
        self.current_drives = drives

    def update_engines(self, engine_info):
        self.active_engines[engine_info["name"]] = engine_info["level"]

    def update_valence_arousal(self, eval):
        self.valence = (self.valence * 0.7) + (eval.get("valence", 0.0) * 0.3)
        self.arousal = (self.arousal * 0.7) + (eval.get("arousal", 0.5) * 0.3)

    def on_plan_generated(self, plan):
        action = plan.get("action")
        if action:
            self.active_plans[action] = {
                "confidence": plan.get("confidence") or plan.get("probability") or 0.0,
                "status": "GENERATED"
            }

    def on_plan_vetted(self, vetting):
        action = vetting.get("plan", {}).get("action")
        if action in self.active_plans:
            self.active_plans[action]["approved"] = vetting.get("approved", False)
            self.active_plans[action]["status"] = "VETTED" if vetting.get("approved") else "BLOCKED"

    def on_utility_assigned(self, data):
        action = data.get("plan", {}).get("action")
        if action in self.active_plans:
            self.active_plans[action]["utility"] = data.get("utility", 0.0)
            self.active_plans[action]["status"] = "VALUED"

    def on_action_command(self, command):
        action = command.get("action")
        if action in self.active_plans:
            self.active_plans[action]["status"] = "EXECUTING"

    def on_action_result(self, result):
        action = result.get("action")
        if action in self.active_plans:
            self.active_plans[action]["status"] = "COMPLETED"
            self.active_plans[action]["result"] = result.get("result")

    def on_action_failure(self, failure):
        action = failure.get("action")
        if action in self.active_plans:
            self.active_plans[action]["status"] = "FAILED"
            self.active_plans[action]["error"] = failure.get("error")

    def get_current_state(self):
        dominant = "CALM"
        if self.active_engines:
            dominant = max(self.active_engines, key=self.active_engines.get)
            
        consciousness_state = None
        if CONSCIOUSNESS_AVAILABLE:
            try:
                consciousness_state = limbic_pb2.ConsciousState(
                    current_focus=self.current_focus,
                    focus_salience=self.focus_salience,
                    self_narrative=self.self_narrative,
                    attention_schema=self.attention_schema
                )
            except: pass

        # Recent Thoughts
        recent_thoughts = []
        if hasattr(self, 'thought_logger'):
            for t in self.thought_logger.recent_thoughts:
                recent_thoughts.append(limbic_pb2.SignedThought(**t))

        kwargs = {
            "arousal": self.arousal,
            "valence": self.valence,
            "drives": self.current_drives,
            "emotions": self.active_engines,
            "dominant_engine": dominant,
            "timestamp": int(time.time()),
            "consciousness": consciousness_state,
            "hormones": self.hormones,
            "phi": self.phi,
            "ego_coherence": self.ego_coherence,
            "meaning": self.meaning,
            "dread": self.dread,
            "age": self.age,
            "plasticity": self.plasticity,
            "vagal_tone": self.vagal_tone,
            "social": limbic_pb2.SocialState(
                reputation=self.social_cognition.reputation.reputation,
                global_trust=self.social_cognition._calculate_global_trust(),
                self_concept=self.social_cognition.reputation.self_concept
            ),
            "economic": limbic_pb2.EconomicState(
                balance=self.economic_engine.balance,
                total_spent=self.economic_engine.total_spent,
                wallet_address=self.wallet.address
            ),
            "recent_thoughts": recent_thoughts
        }
        
        return limbic_pb2.LimbicState(**kwargs)

    async def run(self):
        # Initialize Persistence
        if self.pg_manager:
            await self.pg_manager.connect()
            # Distributed locking to ensure only one instance per agent
            agent_id = os.getenv("AGENT_ID", "default-agent")
            if not await self.pg_manager.acquire_lock(f"limbic-daemon-{agent_id}", str(uuid.uuid4()), ttl=300):
                logger.error(f"Could not acquire lock for agent {agent_id}. Another instance might be running.")
                return

        await self.sql_manager.init_db()
        
        server = grpc.aio.server()
        limbic_pb2_grpc.add_LimbicServiceServicer_to_server(self.servicer, server)
        limbic_pb2_grpc.add_WorkingMemoryServiceServicer_to_server(self.wm_service, server)
        listen_addr = f'[::]:{self.port}'
        server.add_insecure_port(listen_addr)
        
        logger.info(f"Starting gRPC server on {listen_addr}")
        await server.start()
        
        # Run all components
        tasks = [
            asyncio.create_task(self.bus.run()),
            asyncio.create_task(self.wm_service.run()),
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
            asyncio.create_task(self.endocrine.run()),
            asyncio.create_task(self.psych_lattice.run()),
            asyncio.create_task(self.existential_layer.run()),
            asyncio.create_task(self.social_genome.run()),
            asyncio.create_task(self.social_cognition.run()),
            asyncio.create_task(self.consciousness_v2.run()),
            asyncio.create_task(self.vagus_nerve.run()),
            asyncio.create_task(self.pineal_gland.run()),
            asyncio.create_task(self.age_layer.run()),
            asyncio.create_task(self.moral_kernel.run()),
            asyncio.create_task(self.economic_engine.run()),
            asyncio.create_task(self.evolution_engine.run()),
            asyncio.create_task(self.semantic_registry.run()),
        ]

        if CONSCIOUSNESS_AVAILABLE:
            tasks.append(asyncio.create_task(self.consciousness.run()))

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
