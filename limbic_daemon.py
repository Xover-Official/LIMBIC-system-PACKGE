import time
import signal
import sys
import os
import pickle
from limbic_system.core.system import LimbicSystem

class LimbicDaemon:
    def __init__(self, state_file="limbic_state.pkl"):
        self.state_file = state_file
        self.system = LimbicSystem("config/hippocampus_config.json")
        self.running = True
        
        # Load state if exists
        self.load_state()
        
        # Register signals
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)

    def handle_exit(self, signum, frame):
        print(f"Received signal {signum}, shutting down...")
        self.running = False

    def save_state(self):
        print("Saving state...")
        state = {
            'amygdala': {
                'fear': self.system.amygdala.fear,
                'seeking': self.system.amygdala.seeking,
                'arousal': self.system.amygdala.arousal
            },
            'hypothalamus': {
                'energy': self.system.hypothalamus.energy
            },
            'hippocampus_memories': self.system.hippocampus.ca3.network.memories,
            'hippocampus_weights': self.system.hippocampus.ca3.network.weights,
            'importance_map': self.system.hippocampus.consolidation.importance_map
        }
        with open(self.state_file, 'wb') as f:
            pickle.dump(state, f)

    def load_state(self):
        if os.path.exists(self.state_file):
            print("Loading existing state...")
            try:
                with open(self.state_file, 'rb') as f:
                    state = pickle.load(f)
                self.system.amygdala.fear = state['amygdala']['fear']
                self.system.amygdala.seeking = state['amygdala']['seeking']
                self.system.amygdala.arousal = state['amygdala']['arousal']
                self.system.hypothalamus.energy = state['hypothalamus']['energy']
                self.system.hippocampus.ca3.network.memories = state['hippocampus_memories']
                self.system.hippocampus.ca3.network.weights = state['hippocampus_weights']
                self.system.hippocampus.consolidation.importance_map = state['importance_map']
            except Exception as e:
                print(f"Failed to load state: {e}")

    def run(self):
        print("Limbic System Daemon started.")
        self.system.start()
        try:
            while self.running:
                # Simulate a sensory input (64-bit vector of -1 or 1)
                sensory_input = [1 if time.time() % (i+1) > (i+1)/2 else -1 for i in range(64)]
                
                output = self.system.step(sensory_input)
                
                # Periodically save state (every 30 seconds)
                if int(time.time()) % 30 == 0:
                    self.save_state()
                
                # Print status
                temp = self.system.amygdala.get_recall_temperature()
                print(f"Tick: Energy={self.system.hypothalamus.energy:.3f}, Temp={temp:.2f}, Memories={len(self.system.hippocampus.ca3.network.memories)}")
                
                time.sleep(1)
        finally:
            self.save_state()
            self.system.stop()
            print("Limbic System Daemon stopped.")

if __name__ == "__main__":
    daemon = LimbicDaemon()
    daemon.run()
