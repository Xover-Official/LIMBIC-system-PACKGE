import asyncio
from typing import Callable, Dict, List, Any
import logging
from limbic.core.exceptions import CognitiveException

logger = logging.getLogger(__name__)

class LimbicBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.queue = asyncio.Queue()

    def subscribe(self, topic: str, callback: Callable):
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
        logger.debug(f"Subscribed to {topic}")

    async def publish(self, topic: str, data: Any):
        await self.queue.put((topic, data))

    async def run(self):
        logger.info("LimbicBus starting...")
        while True:
            topic, data = await self.queue.get()
            if topic in self.subscribers:
                for callback in self.subscribers[topic]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            async def wrapped_callback(cb, d, t):
                                try:
                                    await cb(d)
                                except CognitiveException as ce:
                                    logger.warning(f"CognitiveException in async callback for topic {t}: {ce}")
                                    await self.publish("SYSTEM_REGRESSION", {"exception": str(ce), "component": ce.component, "severity": ce.severity})
                                except Exception as e:
                                    logger.error(f"Error in async callback for topic {t}: {e}")
                            
                            asyncio.create_task(wrapped_callback(callback, data, topic))
                        else:
                            try:
                                callback(data)
                            except CognitiveException as ce:
                                logger.warning(f"CognitiveException in callback for topic {topic}: {ce}")
                                await self.publish("SYSTEM_REGRESSION", {"exception": str(ce), "component": ce.component, "severity": ce.severity})
                    except Exception as e:
                        logger.error(f"Error in callback invocation for topic {topic}: {e}")
            self.queue.task_done()
