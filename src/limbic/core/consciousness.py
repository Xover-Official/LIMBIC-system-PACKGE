import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class Thalamus:
    """
    Thalamic Gating: Gates information flow to the Global Workspace.
    Filters signals based on salience and current attention.
    """
    def __init__(self, threshold=0.3):
        self.threshold = threshold
        self.attention_bias: Dict[str, float] = {}

    def gate(self, signals: Dict[str, float]) -> Dict[str, float]:
        gated = {}
        for name, level in signals.items():
            bias = self.attention_bias.get(name, 1.0)
            effective_salience = level * bias
            if effective_salience > self.threshold:
                gated[name] = effective_salience
        return gated

    def set_attention(self, topic: str, focus: float):
        self.attention_bias[topic] = 1.0 + focus

class ConsciousnessSystemV2:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.phi = 0.0
        self.active_signals: Dict[str, float] = {}
        self.thalamus = Thalamus(threshold=0.4)
        self.global_workspace: Optional[Dict[str, Any]] = None
        
        # Subscriptions
        self.bus.subscribe("ENGINE_ACTIVE", self.track_signal)
        self.bus.subscribe("DRIVE_UPDATE", self.track_drives)
        self.bus.subscribe("HORMONE_LEVELS", self.track_hormones)
        self.bus.subscribe("PSYCH_STATE", self.track_psych)
        self.bus.subscribe("EXISTENTIAL_STATE", self.track_existential)
        self.bus.subscribe("SEMANTIC_INPUT", self.track_semantic)

    def track_signal(self, data):
        self.active_signals[data["name"]] = data["level"]

    def track_drives(self, drives):
        for k, v in drives.items():
            self.active_signals[f"DRIVE_{k}"] = v

    def track_hormones(self, hormones):
        for k, v in hormones.items():
            self.active_signals[f"HORMONE_{k}"] = v

    def track_psych(self, state):
        self.active_signals["ego_coherence"] = state["ego_coherence"]
        self.active_signals["shadow"] = state["shadow"]

    def track_existential(self, state):
        self.active_signals["meaning"] = state["meaning"]
        self.active_signals["dread"] = state["dread"]

    def track_semantic(self, data):
        self.active_signals["SEMANTIC_VALENCE"] = abs(data["valence"])
        self.active_signals["SEMANTIC_AROUSAL"] = data["arousal"]

    def calculate_phi(self):
        """
        Simplified Integrated Information (Phi) proxy.
        Measures the degree of informational integration among active signals.
        """
        active = [v for v in self.active_signals.values() if v > 0.1]
        if len(active) < 2:
            return 0.0
        
        # Complexity (Number of nodes)
        N = len(active)
        # Integration (Average strength/correlation)
        integration = sum(active) / N
        
        # Phi proxy = Integration * log(Complexity)
        import math
        phi = integration * math.log(N + 1) * 5.0
        return min(phi, 100.0)

    async def run(self):
        logger.info("ConsciousnessSystemV2 (Project Omega) starting...")
        while True:
            self.phi = self.calculate_phi()
            
            # Thalamic Gating
            gated_signals = self.thalamus.gate(self.active_signals)
            
            if gated_signals:
                # Competition for the Global Workspace
                winner_topic = max(gated_signals, key=gated_signals.get)
                winner_salience = gated_signals[winner_topic]
                
                # Global Workspace Broadcast
                self.global_workspace = {
                    "topic": winner_topic,
                    "salience": winner_salience,
                    "phi": self.phi,
                    "content": self.active_signals.get(winner_topic),
                    "timestamp": time.time()
                }
                
                await self.bus.publish("GLOBAL_WORKSPACE", self.global_workspace)
                
                # Top-down attention feedback to Thalamus
                self.thalamus.set_attention(winner_topic, 0.2)
            
            await self.bus.publish("PHI_UPDATE", {"phi": self.phi})
            
            # Slow decay of signals to ensure fresh content
            for k in list(self.active_signals.keys()):
                self.active_signals[k] *= 0.9
                
            await asyncio.sleep(0.5)
