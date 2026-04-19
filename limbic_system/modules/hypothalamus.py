from blinker import signal

class Hypothalamus:
    def __init__(self):
        self.energy = 1.0
        self.homeostasis_signal = signal('homeostasis_signal')

    def tick(self):
        """Simulate metabolic consumption."""
        self.energy -= 0.001
        if self.energy < 0.2:
            self.homeostasis_signal.send(self, trigger='hunger', level=self.energy)
        
        if self.energy < 0.0:
            self.energy = 0.0
            self.homeostasis_signal.send(self, trigger='exhaustion', level=0.0)

    def replenish(self, amount):
        self.energy = min(1.0, self.energy + amount)
