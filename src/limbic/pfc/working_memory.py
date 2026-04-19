import time
import logging
import asyncio
from typing import Dict, List
from limbic.generated import limbic_pb2, limbic_pb2_grpc

logger = logging.getLogger(__name__)

class WorkingMemoryService(limbic_pb2_grpc.WorkingMemoryServiceServicer):
    def __init__(self):
        self.items: Dict[str, limbic_pb2.WorkingMemoryItem] = {}
        self.max_size = 7
        self.default_decay = 0.05

    async def SetItem(self, request, context):
        logger.debug(f"WM: Setting item {request.key}={request.value}")
        item = limbic_pb2.WorkingMemoryItem(
            key=request.key,
            value=request.value,
            decay=request.decay if request.decay > 0 else self.default_decay,
            timestamp=int(time.time())
        )
        self.items[request.key] = item
        self._cleanup()
        return limbic_pb2.WorkingMemoryResponse(success=True)

    async def GetItems(self, request, context):
        self._cleanup()
        return limbic_pb2.WorkingMemoryList(items=list(self.items.values()))

    async def Clear(self, request, context):
        self.items.clear()
        return limbic_pb2.WorkingMemoryResponse(success=True)

    def _cleanup(self):
        now = time.time()
        to_delete = []
        for key, item in self.items.items():
            elapsed = now - item.timestamp
            # Simple exponential decay
            relevance = 2.71828 ** (-item.decay * elapsed)
            if relevance < 0.1:
                to_delete.append(key)
        
        for key in to_delete:
            del self.items[key]
            
        if len(self.items) > self.max_size:
            # Sort by timestamp and keep newest
            sorted_items = sorted(self.items.items(), key=lambda x: x[1].timestamp, reverse=True)
            self.items = dict(sorted_items[:self.max_size])

    async def run(self):
        while True:
            self._cleanup()
            await asyncio.sleep(5)
