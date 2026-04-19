from blinker import signal

class EndocrineSystem:
    def __init__(self, baselines=None):
        if baselines is None:
            baselines = {
                "cortisol": 0.2,
                "oxytocin": 0.5,
                "dopamine": 0.4,
                "serotonin": 0.6
            }
        self.baselines = baselines
        self.hormones = dict(baselines)
        
        self.hormone_update = signal('hormone_update')

    def tick(self):
        """Hormone decay/return to baseline."""
        for hormone, baseline in self.baselines.items():
            # Slowly drift back to baseline
            diff = baseline - self.hormones[hormone]
            self.hormones[hormone] += diff * 0.05
            
        self.hormone_update.send(self, hormones=self.hormones)

    def trigger_release(self, hormone, amount):
        if hormone in self.hormones:
            self.hormones[hormone] = max(0.0, min(1.0, self.hormones[hormone] + amount))
            self.hormone_update.send(self, hormones=self.hormones)

    def get_modulation_factors(self):
        """
        Returns factors that modulate behavior based on hormone levels.
        """
        return {
            # Cortisol increases fear sensitivity
            'fear_sensitivity': 1.0 + self.hormones['cortisol'],
            # Oxytocin increases social bonding / reduces fear
            'social_bonding': self.hormones['oxytocin'],
            'fear_inhibition': self.hormones['oxytocin'] * 0.5,
            # Dopamine increases seeking/reward
            'seeking_drive': 1.0 + self.hormones['dopamine'],
            # Serotonin stabilizes mood/reduces impulsivity
            'mood_stability': self.hormones['serotonin']
        }
