import asyncio
import logging
import time
import numpy as np
import faiss
from typing import List, Dict, Any
from limbic.bus import LimbicBus
from limbic.persistence.vector_store import VectorStore

logger = logging.getLogger(__name__)

class HippocampusV2:
    """
    Hippocampus v2.0: Probabilistic memory store using Bayesian retrieval.
    Computes P(Memory | Context) to decide what to recall.
    """
    def __init__(self, bus: LimbicBus, vector_store: VectorStore):
        self.bus = bus
        self.vs = vector_store
        self.embedding_dim = self.vs.dimension
        self.memory_metadata = self.vs.metadata
        
        self.bus.subscribe("STIMULUS", self.on_stimulus)

    async def on_stimulus(self, stimulus):
        if not stimulus.embedding:
            return

        embedding = np.array(stimulus.embedding).astype('float32').reshape(1, -1)
        
        # 1. Store the new experience
        self.vs.add(stimulus.embedding, {
            "content": stimulus.content,
            "source": stimulus.source,
            "timestamp": time.time()
        })
        
        # Also add to in-memory FAISS index for fast probabilistic retrieval
        if embedding.shape[1] == self.embedding_dim:
            # self.vs.add handles adding to index and metadata
            pass

        # 2. Probabilistic Retrieval: P(Memory_i | Context)
        # Context is the current stimulus
        if self.vs.index.ntotal > 0:
            k = min(5, self.vs.index.ntotal)
            D, I = self.vs.index.search(embedding, k)
            
            # Convert distances to probabilities using softmax of negative distances
            # P(M|C) \propto exp(-dist / temperature)
            temperature = 0.5
            distances = D[0]
            probs = np.exp(-distances / temperature)
            probs /= np.sum(probs)
            
            recalled = []
            for idx, prob in zip(I[0], probs):
                if idx != -1 and prob > 0.1: # Threshold for recall
                    mem = self.memory_metadata[idx]
                    recalled.append({
                        "content": mem["content"],
                        "probability": float(prob),
                        "age": time.time() - mem["timestamp"]
                    })
            
            if recalled:
                logger.info(f"HippocampusV2: Probabilistically recalled {len(recalled)} memories")
                await self.bus.publish("CONTEXT_RECALLED", recalled)

    async def run(self):
        # Could implement consolidation here (transfer from short-term to long-term)
        while True:
            await asyncio.sleep(10)
