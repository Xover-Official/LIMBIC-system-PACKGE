
from typing import Dict, Any
import json

class LimbicCrewAIBridger:
    @staticmethod
    def translate_state_to_persona(limbic_state) -> str:
        """
        Translates a LimbicState (gRPC message) into a textual description 
        that can be injected into a CrewAI Agent's backstory or prompt.
        """
        dominant_emotion = limbic_state.dominant_engine
        arousal = limbic_state.arousal
        valence = limbic_state.valence
        phi = limbic_state.phi
        
        mood = "neutral"
        if valence > 0.5:
            mood = "positive"
        elif valence < -0.5:
            mood = "negative"
            
        intensity = "calm"
        if arousal > 0.7:
            intensity = "agitated"
        elif arousal > 0.4:
            intensity = "alert"
            
        persona_update = (
            f"\nCurrent Emotional State: {dominant_emotion}\n"
            f"Mood: {mood} ({intensity})\n"
            f"Cognitive Integration (Phi): {phi:.2f}\n"
            f"Ego Coherence: {limbic_state.ego_coherence:.2f}\n"
        )
        
        if limbic_state.hormones:
            persona_update += f"Active Hormonal Influences: {', '.join(limbic_state.hormones.keys())}\n"
            
        return persona_update

    @staticmethod
    def get_agent_config_with_limbic_state(agent_name: str, base_backstory: str, limbic_state) -> Dict[str, Any]:
        limbic_context = LimbicCrewAIBridger.translate_state_to_persona(limbic_state)
        return {
            "role": agent_name,
            "backstory": f"{base_backstory}\n\n{limbic_context}",
            "goal": "Operate with biomimetic awareness and execute tasks while maintaining cognitive stability."
        }
