from blinker import signal

class Amygdala:
    def __init__(self):
        self.fear = 0.0
        self.seeking = 0.5
        self.arousal = 0.5
        
        self.emotional_update = signal('emotional_update')

    def update_states(self, fear_delta=0.0, seeking_delta=0.0, arousal_delta=0.0):
        self.fear = max(0.0, min(1.0, self.fear + fear_delta))
        self.seeking = max(0.0, min(1.0, self.seeking + seeking_delta))
        self.arousal = max(0.0, min(1.0, self.arousal + arousal_delta))
        
        self.emotional_update.send(self, state={
            'fear': self.fear,
            'seeking': self.seeking,
            'arousal': self.arousal
        })

    def get_recall_temperature(self):
        """
        Fear -> Low Temp (Deterministic/Safety)
        Seeking -> High Temp (Stochastic/Creative)
        """
        # Base temperature is 1.0
        # High fear reduces temperature towards 0.1
        # High seeking increases temperature towards 3.0
        temp = 1.0
        temp -= self.fear * 0.9
        temp += self.seeking * 2.0
        return max(0.1, temp)
