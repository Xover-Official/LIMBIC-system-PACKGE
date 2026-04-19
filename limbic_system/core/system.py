import json
import os
from limbic_system.modules.hippocampus.regions import DentateGyrus, CA3Region, CA1Region
from limbic_system.modules.hippocampus.consolidation import ConsolidationEngine
from limbic_system.modules.amygdala import Amygdala
from limbic_system.modules.hypothalamus import Hypothalamus
from limbic_system.modules.somatosensory import SomatosensoryCortex
from limbic_system.modules.endocrine import EndocrineSystem
from limbic_system.modules.social import SocialLogic

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
    def __init__(self, config_path, genome_path="config/genome_manifest.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.genome = {}
        if os.path.exists(genome_path):
            with open(genome_path, 'r') as f:
                self.genome = json.load(f)
        
        self.amygdala = Amygdala()
        self.hypothalamus = Hypothalamus(metabolic_rates=self.genome.get('metabolic_rates'))
        self.hippocampus = Hippocampus(size=64, config=self.config) # Fixed size for demo
        self.somatosensory = SomatosensoryCortex()
        self.endocrine = EndocrineSystem(baselines=self.genome.get('hormonal_baselines'))
        self.social = SocialLogic()
        
        # Connect signals
        self.amygdala.emotional_update.connect(self._on_emotional_update)
        self.hypothalamus.homeostasis_signal.connect(self._on_homeostasis)
        self.hypothalamus.circadian_signal.connect(self._on_circadian)
        self.somatosensory.somatosensory_update.connect(self._on_somatosensory)
        self.endocrine.hormone_update.connect(self._on_hormone_update)
        self.social.social_update.connect(self._on_social_update)

    def _on_emotional_update(self, sender, **kwargs):
        state = kwargs.get('state', {})
        # High fear triggers cortisol release
        if state.get('fear', 0) > 0.7:
            self.endocrine.trigger_release('cortisol', 0.1)
        # High seeking triggers dopamine
        if state.get('seeking', 0) > 0.7:
            self.endocrine.trigger_release('dopamine', 0.1)

    def _on_homeostasis(self, sender, **kwargs):
        trigger = kwargs.get('trigger')
        if trigger == 'hunger':
            self.amygdala.update_states(seeking_delta=0.1)
        elif trigger == 'exhaustion':
            self.amygdala.update_states(fear_delta=0.1)

    def _on_circadian(self, sender, **kwargs):
        # Drowsiness increases fear/irritability or reduces arousal
        if kwargs.get('trigger') == 'drowsiness':
            self.amygdala.update_states(arousal_delta=-0.05, fear_delta=0.05)
        
        # REM state influences hippocampal temperature/stochasticity
        self.rem_state = kwargs.get('rem_state', 0.0)

    def _on_somatosensory(self, sender, **kwargs):
        pass

    def _on_hormone_update(self, sender, **kwargs):
        pass

    def _on_social_update(self, sender, **kwargs):
        pass

    def start(self):
        self.hippocampus.start()

    def stop(self):
        self.hippocampus.stop()

    def step(self, sensory_input, physiological_input=None, social_stimulus=None):
        # 1. Process physiological input
        if physiological_input:
            phys_deltas = self.somatosensory.process_physiological_input(physiological_input)
            self.amygdala.update_states(
                fear_delta=phys_deltas['fear'],
                arousal_delta=phys_deltas['arousal'],
                seeking_delta=phys_deltas['seeking']
            )

        # 2. Process social stimulus
        if social_stimulus:
            # social_stimulus expected to be (type, magnitude)
            social_deltas = self.social.process_social_stimulus(*social_stimulus)
            self.amygdala.update_states(
                fear_delta=social_deltas.get('fear', 0),
                arousal_delta=social_deltas.get('arousal', 0),
                seeking_delta=social_deltas.get('seeking', 0)
            )
            # Endocrine effects from social
            if social_deltas.get('cortisol'):
                self.endocrine.trigger_release('cortisol', social_deltas['cortisol'])
            if social_deltas.get('oxytocin'):
                self.endocrine.trigger_release('oxytocin', social_deltas['oxytocin'])
            if social_deltas.get('dopamine'):
                self.endocrine.trigger_release('dopamine', social_deltas['dopamine'])

        # 3. Update modules
        self.hypothalamus.tick()
        self.endocrine.tick()
        
        # 3. Apply hormonal modulation
        modulators = self.endocrine.get_modulation_factors()
        # (In a real system, we'd use these to scale deltas)
        
        # 4. Process sensory input through hippocampus
        temp = self.amygdala.get_recall_temperature()
        
        # If sleeping and in REM, increase temperature for "dreaming"
        if self.hypothalamus.is_sleeping:
            temp += self.rem_state * 2.0
            
        return self.hippocampus.process_input(sensory_input, temp)
