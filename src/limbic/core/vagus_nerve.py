import asyncio
import logging
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class VagusNerve:
    """
    Biomimetic Vagus Nerve: The primary conduit for interoceptive feedback
    and parasympathetic control. Couples the 'body' state to the 'brain'.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.tone = 0.5  # 0.0 to 1.0, higher means more parasympathetic (calm)
        self.heart_rate_variability = 0.5
        
        # Subscribe to internal body signals
        self.bus.subscribe("INTERNAL_FEELING", self.on_internal_feeling)
        self.bus.subscribe("HORMONE_LEVELS", self.on_hormone_levels)
        self.bus.subscribe("ENGINE_ACTIVE", self.on_engine_active)

    async def on_internal_feeling(self, feelings):
        # Negative feelings (HUNGRY, ANXIOUS) decrease vagal tone
        if any(f in ["HUNGRY", "ANXIOUS", "PAIN"] for f in feelings):
            self.tone = max(0.0, self.tone - 0.1)
        else:
            self.tone = min(1.0, self.tone + 0.05)
        await self.broadcast_state()

    async def on_hormone_levels(self, hormones):
        # High adrenaline/cortisol decreases vagal tone
        stress = (hormones.get("adrenaline", 0) + hormones.get("cortisol", 0)) / 2
        self.tone = max(0.0, min(1.0, self.tone - (stress * 0.1)))
        await self.broadcast_state()

    async def on_engine_active(self, engine_info):
        # Fear and Panic significantly drop vagal tone
        if engine_info["name"] in ["FEAR", "PANIC"] and engine_info["level"] > 0.5:
            self.tone = max(0.0, self.tone - (engine_info["level"] * 0.2))
        elif engine_info["name"] == "CARE" and engine_info["level"] > 0.5:
            self.tone = min(1.0, self.tone + (engine_info["level"] * 0.1))
        await self.broadcast_state()

    async def broadcast_state(self):
        await self.bus.publish("VAGAL_TONE", {
            "tone": self.tone,
            "state": "PARASYMPATHETIC" if self.tone > 0.6 else "SYMPATHETIC" if self.tone < 0.4 else "NEUTRAL"
        })

    async def run(self):
        logger.info("VagusNerve starting...")
        while True:
            # Homeostatic tendency towards neutral tone
            self.tone += (0.5 - self.tone) * 0.01
            await self.broadcast_state()
            await asyncio.sleep(2)
