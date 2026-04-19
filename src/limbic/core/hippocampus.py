import asyncio
from limbic.bus import LimbicBus
from limbic.persistence.vector_store import VectorStore

class Hippocampus:
    def __init__(self, bus: LimbicBus, vector_store: VectorStore):
        self.bus = bus
        self.vs = vector_store
        self.bus.subscribe("STIMULUS", self.on_stimulus)

    async def on_stimulus(self, stimulus):
        if stimulus.embedding:
            # Search for similar past experiences
            results = self.vs.search(stimulus.embedding)
            if results:
                await self.bus.publish("CONTEXT_RECALLED", results)
            
            # Store new experience
            self.vs.add(stimulus.embedding, {
                "content": stimulus.content,
                "source": stimulus.source,
                "timestamp": asyncio.get_event_loop().time()
            })
