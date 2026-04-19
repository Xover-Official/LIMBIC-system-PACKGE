import json
from limbic_system.modules.hippocampus.regions import DentateGyrus, CA3Region, CA1Region
from limbic_system.modules.hippocampus.consolidation import ConsolidationEngine
from limbic_system.modules.amygdala import Amygdala
from limbic_system.modules.hypothalamus import Hypothalamus

class Hippocampus:
    def __init__(self, size, config):
        self.dg = DentateGyrus(config)
        self.ca3 = CA3Region(size, config)
        self.ca1 = CA1Region(config)
        self.consolidation = ConsolidationEngine(self, config)
    
    def start(self):
        self.consolidation.start()
    
    def stop(self):
        self.consolidation.stop()

    def process_input(self, vector, temperature):
        # DG: Pattern separation
        separated = self.dg.process(vector)
        # CA3: Pattern completion/association
        # If we are in "learning" mode, we'd associate. 
        # For simplicity, let's say we always try to recall and then learn.
        recalled = self.ca3.recall(separated, temperature)
        # CA1: Decode
        output = self.ca1.decode(recalled, temperature)
        
        # Hebbian reinforcement
        self.ca3.associate(output)
        return output

class LimbicSystem:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.amygdala = Amygdala()
        self.hypothalamus = Hypothalamus()
        self.hippocampus = Hippocampus(size=64, config=self.config) # Fixed size for demo
        
        # Connect signals
        self.amygdala.emotional_update.connect(self._on_emotional_update)
        self.hypothalamus.homeostasis_signal.connect(self._on_homeostasis)

    def _on_emotional_update(self, sender, **kwargs):
        # Update system state based on emotions
        pass

    def _on_homeostasis(self, sender, **kwargs):
        trigger = kwargs.get('trigger')
        if trigger == 'hunger':
            self.amygdala.update_states(seeking_delta=0.1)
        elif trigger == 'exhaustion':
            self.amygdala.update_states(fear_delta=0.1)

    def start(self):
        self.hippocampus.start()

    def stop(self):
        self.hippocampus.stop()

    def step(self, sensory_input):
        self.hypothalamus.tick()
        temp = self.amygdala.get_recall_temperature()
        return self.hippocampus.process_input(sensory_input, temp)
