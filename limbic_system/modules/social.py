from blinker import signal

class SocialLogic:
    def __init__(self):
        self.social_status = 0.5
        self.tribal_alignment = 0.5
        self.social_update = signal('social_update')

    def process_social_stimulus(self, stimulus_type, magnitude):
        """
        stimulus_type: 'praise', 'insult', 'inclusion', 'exclusion'
        magnitude: 0.0 to 1.0
        """
        deltas = {'fear': 0.0, 'seeking': 0.0, 'arousal': 0.0, 'cortisol': 0.0, 'oxytocin': 0.0, 'dopamine': 0.0}
        
        if stimulus_type == 'praise':
            self.social_status = min(1.0, self.social_status + magnitude * 0.1)
            deltas['dopamine'] += magnitude * 0.2
            deltas['seeking'] += magnitude * 0.1
        elif stimulus_type == 'insult':
            self.social_status = max(0.0, self.social_status - magnitude * 0.1)
            deltas['cortisol'] += magnitude * 0.2
            deltas['fear'] += magnitude * 0.1
        elif stimulus_type == 'inclusion':
            self.tribal_alignment = min(1.0, self.tribal_alignment + magnitude * 0.1)
            deltas['oxytocin'] += magnitude * 0.3
            deltas['fear'] -= magnitude * 0.1
        elif stimulus_type == 'exclusion':
            self.tribal_alignment = max(0.0, self.tribal_alignment - magnitude * 0.1)
            deltas['cortisol'] += magnitude * 0.3
            deltas['fear'] += magnitude * 0.2

        self.social_update.send(self, status=self.social_status, tribalism=self.tribal_alignment)
        return deltas
