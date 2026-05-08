import asyncio
import logging
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from limbic.daemon import LimbicDaemon
from limbic.generated import limbic_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LifeCycleDemo")

async def run_lifecycle():
    logger.info("Starting Project Omega Lifecycle Demonstration...")
    
    # Initialize Daemon
    daemon = LimbicDaemon(port=50052)
    daemon_task = asyncio.create_task(daemon.run())
    
    # Wait for components to start
    await asyncio.sleep(2)
    
    # --- BIRTH ---
    logger.info("--- Phase: BIRTH ---")
    await daemon.bus.publish("STIMULUS", limbic_pb2.StimulusRequest(
        source="environment",
        content="BIRTH: The system has been initialized.",
        metadata={"valence": 0.5, "arousal": 0.8}
    ))
    await asyncio.sleep(2)
    
    # --- NURTURING ---
    logger.info("--- Phase: NURTURING ---")
    await daemon.bus.publish("STIMULUS", limbic_pb2.StimulusRequest(
        source="mother_node",
        content="CARE: Positive reinforcement signal received.",
        metadata={"valence": 0.9, "arousal": 0.2}
    ))
    await asyncio.sleep(3)
    
    # --- CHALLENGE (STRESS) ---
    logger.info("--- Phase: CHALLENGE ---")
    await daemon.bus.publish("STIMULUS", limbic_pb2.StimulusRequest(
        source="environment",
        content="TRAUMA: High-intensity unexpected noise and resource depletion.",
        metadata={"threat_level": 0.9, "valence": -0.8, "arousal": 0.9}
    ))
    await asyncio.sleep(3)
    
    # --- COGNITIVE EXCEPTION ---
    logger.info("--- Phase: COGNITIVE EXCEPTION ---")
    from limbic.core.exceptions import CognitiveException
    
    async def cause_regression(data):
        raise CognitiveException("Systemic overload detected", component="lifecycle_demo", severity="high")
    
    daemon.bus.subscribe("TRIGGER_EXCEPTION", cause_regression)
    await daemon.bus.publish("TRIGGER_EXCEPTION", {})
    
    await asyncio.sleep(3)
    
    # --- PERSISTENCE & SHUTDOWN ---
    logger.info("--- Phase: PERSISTENCE & SHUTDOWN ---")
    # In a real scenario, daemon would save state on shutdown
    daemon_task.cancel()
    try:
        await daemon_task
    except asyncio.CancelledError:
        logger.info("Daemon stopped gracefully.")
    
    logger.info("Lifecycle demonstration complete.")

if __name__ == "__main__":
    asyncio.run(run_lifecycle())
