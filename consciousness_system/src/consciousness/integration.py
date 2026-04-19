import asyncio
import logging
from limbic.bus import LimbicBus
from .gwt import GlobalWorkspace
from .self import SelfModel
from .metacognition import MetacognitiveMonitor

logger = logging.getLogger(__name__)

class ConsciousnessSystem:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.gwt = GlobalWorkspace(bus)
        self.self_model = SelfModel(bus)
        self.monitor = MetacognitiveMonitor(bus)

    async def run(self):
        logger.info("Consciousness System integration layer starting...")
        tasks = [
            asyncio.create_task(self.gwt.run()),
            asyncio.create_task(self.self_model.run()),
            asyncio.create_task(self.monitor.run()),
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
            raise
