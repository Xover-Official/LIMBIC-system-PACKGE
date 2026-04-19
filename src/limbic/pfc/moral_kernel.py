import logging
import json
from typing import List, Dict, Any
from cryptography.hazmat.primitives.asymmetric import ed25519
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class MoralKernel:
    def __init__(self, bus: LimbicBus, public_key_hex: str = None, axioms_file: str = "config/axioms.json"):
        self.bus = bus
        self.axioms_file = axioms_file
        self.public_key_hex = public_key_hex
        self.public_key = None
        if public_key_hex:
            self.public_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        self.axioms: List[Dict[str, Any]] = []

    async def run(self):
        logger.info("Moral Kernel starting...")
        self.load_and_verify_axioms()
        
        self.bus.subscribe("CANDIDATE_PLAN", self.evaluate_plan)
        self.bus.subscribe("WORKSPACE_BROADCAST", self.monitor_consciousness)

    def load_and_verify_axioms(self):
        try:
            with open(self.axioms_file, 'r') as f:
                data = json.load(f)
            
            manifest = data["axioms"]
            if self.public_key:
                signature = bytes.fromhex(data["signature"])
                manifest_bytes = json.dumps(manifest, sort_keys=True).encode()
                self.public_key.verify(signature, manifest_bytes)
                logger.info(f"Verified {len(manifest)} moral axioms with signature.")
            else:
                logger.warning("No public key provided, axioms will not be cryptographically verified.")
            
            self.axioms = manifest
        except FileNotFoundError:
            logger.error(f"Axioms file not found: {self.axioms_file}")
        except Exception as e:
            logger.error(f"Failed to verify moral axioms: {e}")

    async def evaluate_plan(self, plan: Dict[str, Any]):
        action = plan.get("action", "unknown")
        for axiom in self.axioms:
            if self._violates_axiom(plan, axiom):
                logger.warning(f"VETO: Plan '{action}' violates axiom: {axiom.get('statement', 'Unknown')}")
                await self.bus.publish("VETO", {
                    "plan": plan,
                    "axiom": axiom.get("statement"),
                    "reason": "Moral violation detected"
                })
                await self.bus.publish("PLAN_VETTED", {
                    "plan": plan,
                    "approved": False,
                    "reason": f"Axiom violation: {axiom.get('statement')}"
                })
                return

    def _violates_axiom(self, plan: Dict[str, Any], axiom: Dict[str, Any]) -> bool:
        # Example: forbidden_actions list in axiom
        forbidden = axiom.get("forbidden_actions", [])
        if plan.get("action") in forbidden:
            return True
        # Example: required keywords in plan
        must_contain = axiom.get("must_contain_keywords", [])
        if must_contain:
            plan_str = json.dumps(plan).lower()
            for kw in must_contain:
                if kw.lower() not in plan_str:
                    return True # Violates if it doesn't contain required keywords
        return False

    async def monitor_consciousness(self, broadcast: Dict[str, Any]):
        # Moral monitoring of consciousness thoughts
        pass
