
from typing import TypedDict, Dict, Any

class LimbicStateMetadata(TypedDict):
    arousal: float
    valence: float
    dominant_engine: str
    phi: float
    hormones: Dict[str, float]

class LimbicLangGraphState:
    @staticmethod
    def inject_limbic_metadata(graph_state: Dict[str, Any], limbic_state) -> Dict[str, Any]:
        """
        Injects limbic system metadata into the LangGraph shared state.
        """
        metadata: LimbicStateMetadata = {
            "arousal": limbic_state.arousal,
            "valence": limbic_state.valence,
            "dominant_engine": limbic_state.dominant_engine,
            "phi": limbic_state.phi,
            "hormones": dict(limbic_state.hormones)
        }
        
        graph_state["limbic_metadata"] = metadata
        return graph_state

    @staticmethod
    def get_limbic_bias_prompt(graph_state: Dict[str, Any]) -> str:
        """
        Generates a prompt snippet based on limbic metadata to bias LLM nodes.
        """
        metadata = graph_state.get("limbic_metadata")
        if not metadata:
            return ""
            
        bias = f"Internal State: {metadata['dominant_engine']}. "
        if metadata['arousal'] > 0.8:
            bias += "You are under high stress. Be concise and urgent."
        elif metadata['valence'] < -0.5:
            bias += "Your outlook is pessimistic. Focus on risks."
        elif metadata['valence'] > 0.5:
            bias += "Your outlook is optimistic. Focus on opportunities."
            
        return bias
