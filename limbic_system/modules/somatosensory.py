from blinker import signal

class SomatosensoryCortex:
    def __init__(self):
        self.pain = 0.0
        self.temperature = 0.5  # 0.5 is normal
        self.heart_rate = 60.0  # BPM
        
        self.somatosensory_update = signal('somatosensory_update')

    def process_physiological_input(self, phys_vector):
        """
        Processes a vector of physiological data.
        Expected format: [pain, temperature, heart_rate_normalized]
        """
        if len(phys_vector) >= 1:
            self.pain = max(0.0, min(1.0, phys_vector[0]))
        if len(phys_vector) >= 2:
            self.temperature = max(0.0, min(1.0, phys_vector[1]))
        if len(phys_vector) >= 3:
            # heart_rate_normalized: 0.0 -> 40 BPM, 1.0 -> 200 BPM
            self.heart_rate = 40.0 + (phys_vector[2] * 160.0)

        self.somatosensory_update.send(self, state={
            'pain': self.pain,
            'temperature': self.temperature,
            'heart_rate': self.heart_rate
        })
        
        return self._map_to_limbic_deltas()

    def _map_to_limbic_deltas(self):
        """
        Maps current physiological state to suggested deltas for the limbic system.
        """
        deltas = {
            'fear': 0.0,
            'arousal': 0.0,
            'seeking': 0.0
        }
        
        # Pain increases fear and arousal
        if self.pain > 0.2:
            deltas['fear'] += self.pain * 0.5
            deltas['arousal'] += self.pain * 0.8
            
        # Abnormal temperature increases arousal (stress)
        temp_diff = abs(self.temperature - 0.5)
        if temp_diff > 0.2:
            deltas['arousal'] += temp_diff * 0.5
            
        # High heart rate correlates with arousal
        if self.heart_rate > 100:
            deltas['arousal'] += (self.heart_rate - 100) / 100.0 * 0.3
            
        return deltas
