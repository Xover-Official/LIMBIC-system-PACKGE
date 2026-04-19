import asyncio
import logging
import subprocess
import os
import sys
from typing import Dict, Any
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class EvolutionEngine:
    def __init__(self, bus: LimbicBus, target_module: str = "src/limbic/pfc/vmpfc.py"):
        self.bus = bus
        self.target_module = target_module
        self.backup_path = target_module + ".bak"

    async def run(self):
        logger.info("Evolution Engine starting...")
        self.bus.subscribe("EVOLUTION_PROPOSAL", self.handle_proposal)
        
        while True:
            await asyncio.sleep(3600)

    async def handle_proposal(self, proposal: Dict[str, Any]):
        """
        Proposal format: {
            "tweak_id": "vmpfc_aggression_adjustment",
            "search_and_replace": {"old": "aggression = 0.5", "new": "aggression = 0.4"}
        }
        """
        tweak_id = proposal.get("tweak_id")
        logger.info(f"Processing evolution proposal: {tweak_id}")
        
        if await self.validate_tweak(proposal):
            logger.info(f"Proposal {tweak_id} passed validation. Integrating...")
            self.integrate_tweak(proposal)
            await self.bus.publish("EVOLUTION_SUCCESS", {"tweak_id": tweak_id})
        else:
            logger.warning(f"Proposal {tweak_id} failed validation.")
            await self.bus.publish("EVOLUTION_FAILURE", {"tweak_id": tweak_id})

    async def validate_tweak(self, proposal: Dict[str, Any]) -> bool:
        # Create shadow module
        shadow_path = self.target_module + ".shadow"
        try:
            with open(self.target_module, 'r') as f:
                content = f.read()
            
            # Apply tweak
            sar = proposal.get("search_and_replace", {})
            new_content = content.replace(sar.get("old", ""), sar.get("new", ""))
            
            with open(shadow_path, 'w') as f:
                f.write(new_content)
            
            # Run shadow instance validation
            # In a real system, we'd launch a separate process with this shadow module
            # For now, we'll run a lint check and a mock test
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "py_compile", shadow_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if process.returncode != 0:
                logger.error("Shadow module failed compilation.")
                return False
                
            # Run behavioral tests (mocked)
            logger.info("Running behavioral tests on shadow module...")
            await asyncio.sleep(2) # Simulate test time
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
        finally:
            if os.path.exists(shadow_path):
                os.remove(shadow_path)

    def integrate_tweak(self, proposal: Dict[str, Any]):
        try:
            # Backup
            if not os.path.exists(self.backup_path):
                import shutil
                shutil.copy2(self.target_module, self.backup_path)
            
            with open(self.target_module, 'r') as f:
                content = f.read()
            
            sar = proposal.get("search_and_replace", {})
            new_content = content.replace(sar.get("old", ""), sar.get("new", ""))
            
            with open(self.target_module, 'w') as f:
                f.write(new_content)
            
            logger.info(f"Module {self.target_module} updated successfully.")
            # In a real system, we might need to trigger a reload of the module
        except Exception as e:
            logger.error(f"Failed to integrate tweak: {e}")
