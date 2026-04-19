import asyncio
import logging
import grpc
import time
from concurrent import futures
from limbic.bus import LimbicBus
from limbic.generated import limbic_pb2_grpc, limbic_pb2
from limbic.core.hypothalamus import Hypothalamus
from limbic.core.amygdala import Amygdala
from limbic.core.hippocampus import Hippocampus
from limbic.core.nucleus_accumbens import NucleusAccumbens
from limbic.core.insula import Insula
from limbic.persistence.sqlite_manager import SQLiteManager, EventLogger
from limbic.persistence.vector_store import VectorStore
from limbic.engines.seeking import SeekingEngine
from limbic.engines.fear import FearEngine
from limbic.engines.panic import PanicEngine
from limbic.engines.care import CareEngine

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

class LimbicDaemon:
    def __init__(self, port=50051):
        self.port = port
        self.bus = LimbicBus()
        self.servicer = LimbicServicer(self.bus, self)
        
        # Core
        self.hypothalamus = Hypothalamus(self.bus)
        self.amygdala = Amygdala(self.bus)
        self.vs = VectorStore()
        self.hippocampus = Hippocampus(self.bus, self.vs)
        self.na = NucleusAccumbens(self.bus)
        self.insula = Insula(self.bus)
        
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
        
        # Current Global State
        self.arousal = 0.5
        self.valence = 0.0
        self.current_drives = {}
        self.active_engines = {}
        
        # Subscribe to updates for global state
        self.bus.subscribe("DRIVE_UPDATE", self.update_drives)
        self.bus.subscribe("ENGINE_ACTIVE", self.update_engines)
        self.bus.subscribe("SIGNIFICANCE_EVALUATED", self.update_valence_arousal)

    def update_drives(self, drives):
        self.current_drives = drives

    def update_engines(self, engine_info):
        self.active_engines[engine_info["name"]] = engine_info["level"]

    def update_valence_arousal(self, eval):
        # Rolling average or similar for global state
        self.valence = (self.valence * 0.7) + (eval["valence"] * 0.3)
        self.arousal = (self.arousal * 0.7) + (eval["arousal"] * 0.3)

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
            asyncio.create_task(self.engines["SEEKING"].run()),
            asyncio.create_task(self.engines["FEAR"].run()),
            asyncio.create_task(self.engines["PANIC"].run()),
            asyncio.create_task(self.engines["CARE"].run()),
        ]
        
        try:
            await server.wait_for_termination()
        except asyncio.CancelledError:
            for t in tasks: t.cancel()
            await server.stop(0)
