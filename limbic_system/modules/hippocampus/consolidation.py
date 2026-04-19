import time
import threading
from limbic_system.utils.stochastic import StochasticEngine

class ConsolidationEngine:
    def __init__(self, hippocampus, config):
        self.hippocampus = hippocampus
        self.pruning_threshold = config.get("pruning_threshold", 0.1)
        self.decay_rate = config.get("decay_rate", 0.01)
        self.interval = config.get("consolidation_interval", 60)
        self.importance_map = {} # pattern_index -> importance
        self.running = False
        self._thread = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def _run(self):
        while self.running:
            time.sleep(self.interval)
            self.consolidate()

    def consolidate(self):
        """Pruning based on importance decay and replay."""
        # 1. Decay importance
        for idx in list(self.importance_map.keys()):
            self.importance_map[idx] -= self.decay_rate
            if self.importance_map[idx] < self.pruning_threshold:
                # Stochastic pruning
                if StochasticEngine.gaussian(0.5, 0.2) > 0.6:
                    del self.importance_map[idx]
                    # Note: Actually removing from attractor weights is complex in Hebbian
                    # For this implementation, we just manage the 'memories' list
                    if idx < len(self.hippocampus.ca3.network.memories):
                        # In a real system, we'd re-calculate weights.
                        # For simplicity, we just mark it as pruned.
                        pass

        # 2. Replay
        if self.hippocampus.ca3.network.memories:
            replay_idx = StochasticEngine.poisson(len(self.hippocampus.ca3.network.memories) / 2)
            replay_idx = min(replay_idx, len(self.hippocampus.ca3.network.memories) - 1)
            pattern = self.hippocampus.ca3.network.memories[replay_idx]
            # Reinforce
            self.hippocampus.ca3.associate(pattern)
            self.importance_map[replay_idx] = self.importance_map.get(replay_idx, 1.0) + 0.1

    def record_access(self, pattern_idx):
        self.importance_map[pattern_idx] = self.importance_map.get(pattern_idx, 1.0) + 0.2
