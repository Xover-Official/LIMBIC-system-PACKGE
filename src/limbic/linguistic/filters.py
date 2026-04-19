import asyncio
import logging
import re
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class WernickeFilter:
    """
    Input linguistic filter: Decodes semantics and extracts emotional tone
    from incoming linguistic stimuli.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.bus.subscribe("STIMULUS", self.process_input)

    async def process_input(self, request):
        content = getattr(request, 'content', "")
        if not content or not isinstance(content, str):
            return

        # Simple sentiment/semantic analysis
        valence = 0.0
        arousal = 0.0
        
        positive_words = ["happy", "good", "great", "love", "friend", "safe"]
        negative_words = ["sad", "bad", "hate", "enemy", "danger", "fear", "hurt"]
        intense_words = ["very", "extremely", "now", "stop", "urgent", "!"]

        for word in positive_words:
            if word in content.lower(): valence += 0.2
        for word in negative_words:
            if word in content.lower(): valence -= 0.2
        for word in intense_words:
            if word in content.lower(): arousal += 0.3

        # Publish semantic extraction
        await self.bus.publish("SEMANTIC_INPUT", {
            "content": content,
            "valence": max(-1.0, min(1.0, valence)),
            "arousal": max(0.0, min(1.0, arousal))
        })

class BrocaFilter:
    """
    Output linguistic filter: Ensures produced language conforms to 
    the current emotional and developmental state.
    """
    def __init__(self, bus: LimbicBus):
        self.bus = bus
        self.current_valence = 0.0
        self.current_arousal = 0.0
        self.bus.subscribe("SIGNIFICANCE_EVALUATED", self.update_state)

    async def update_state(self, eval):
        self.current_valence = eval["valence"]
        self.current_arousal = eval["arousal"]

    def filter_output(self, text: str) -> str:
        # If highly aroused, maybe add exclamation marks or capitalize
        if self.current_arousal > 0.8:
            text = text.upper() + "!!!"
        elif self.current_valence < -0.5:
            text = text + "... (sigh)"
        
        return text

    async def process_response_request(self, data):
        original_text = data.get("text", "")
        filtered_text = self.filter_output(original_text)
        await self.bus.publish("LINGUISTIC_OUTPUT", {
            "original": original_text,
            "filtered": filtered_text
        })
