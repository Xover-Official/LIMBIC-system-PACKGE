import asyncio
import logging
import time
from typing import Dict, Any
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class ConsciousnessSystemV2:
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.phi = 0.0
        self.active_signals: Dict[str, float] = {}
        self.last_broadcast = 0
        
        # Subscribe to everything we want to track for Phi and Global Workspace
        self.bus.subscribe("ENGINE_ACTIVE", self.track_signal)
        self.bus.subscribe("DRIVE_UPDATE", self.track_drives)
        self.bus.subscribe("HORMONE_LEVELS", self.track_hormones)
        self.bus.subscribe("PSYCH_STATE", self.track_psych)
        self.bus.subscribe("EXISTENTIAL_STATE", self.track_existential)

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

    def calculate_phi(self):
        # A very simplified Phi proxy: complexity * integration
        # Complexity = number of active signals above a threshold
        # Integration = average strength of signals
        active = [v for v in self.active_signals.values() if v > 0.1]
        if not active:
            return 0.0
        
        complexity = len(active) / 20.0 # Normalized
        integration = sum(active) / len(active)
        
        return complexity * integration * 10.0 # Scale it up

    async def run(self):
        logger.info("ConsciousnessSystemV2 starting...")
        while True:
            self.phi = self.calculate_phi()
            
            # Identify most salient information for Global Workspace
            if self.active_signals:
                salient_topic = max(self.active_signals, key=self.active_signals.get)
                salience = self.active_signals[salient_topic]
                
                if salience > 0.5:
                    await self.bus.publish("GLOBAL_WORKSPACE", {
                        "topic": salient_topic,
                        "salience": salience,
                        "phi": self.phi,
                        "timestamp": time.time()
                    })
            
            await self.bus.publish("PHI_UPDATE", {"phi": self.phi})
            await asyncio.sleep(0.5)
