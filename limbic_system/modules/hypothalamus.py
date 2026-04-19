from blinker import signal

class Hypothalamus:
    def __init__(self, metabolic_rates=None):
        self.energy = 1.0
        self.sleep_pressure = 0.0
        self.is_sleeping = False
        self.rem_state = 0.0  # 0.0 to 1.0
        
        self.rates = metabolic_rates or {
            "energy_decay": 0.001,
            "sleep_pressure_gain": 0.005
        }
        
        self.homeostasis_signal = signal('homeostasis_signal')
        self.circadian_signal = signal('circadian_signal')

    def tick(self):
        """Simulate metabolic consumption and circadian rhythm."""
        if not self.is_sleeping:
            self.energy -= self.rates["energy_decay"]
            self.sleep_pressure += self.rates["sleep_pressure_gain"]
            self.rem_state = 0.0
        else:
            # During sleep, energy replenishes slowly and sleep pressure drops
            self.energy += self.rates["energy_decay"] * 0.5
            self.sleep_pressure -= self.rates["sleep_pressure_gain"] * 2.0
            
            # REM state cycle during sleep
            # Simple oscillating REM state
            import math
            import time
            self.rem_state = (math.sin(time.time() / 10.0) + 1.0) / 2.0

        # Bound values
        self.energy = max(0.0, min(1.0, self.energy))
        self.sleep_pressure = max(0.0, min(2.0, self.sleep_pressure)) # Can go above 1.0 for extreme sleepiness

        if self.energy < 0.2:
            self.homeostasis_signal.send(self, trigger='hunger', level=self.energy)
        
        if self.energy < 0.01:
            self.homeostasis_signal.send(self, trigger='exhaustion', level=0.0)

        if self.sleep_pressure > 0.8:
            self.circadian_signal.send(self, trigger='drowsiness', level=self.sleep_pressure)
            
        self.circadian_signal.send(self, 
                                  sleep_pressure=self.sleep_pressure, 
                                  is_sleeping=self.is_sleeping,
                                  rem_state=self.rem_state)

    def set_sleep(self, sleeping: bool):
        self.is_sleeping = sleeping

    def replenish(self, amount):
        self.energy = min(1.0, self.energy + amount)
