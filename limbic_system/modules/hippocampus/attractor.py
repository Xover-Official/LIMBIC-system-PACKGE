import random
import math
from limbic_system.utils.stochastic import StochasticEngine

class ProbabilisticAttractorNetwork:
    def __init__(self, size):
        self.size = size
        # Initialize weights with zeros
        self.weights = [[0.0 for _ in range(size)] for _ in range(size)]
        self.memories = []

    def train(self, pattern):
        """Hebbian learning rule."""
        if len(pattern) != self.size:
            raise ValueError("Pattern size mismatch")
        
        for i in range(self.size):
            for j in range(self.size):
                if i != j:
                    self.weights[i][j] += pattern[i] * pattern[j]
        self.memories.append(pattern)

    def energy(self, state):
        e = 0.0
        for i in range(self.size):
            for j in range(self.size):
                e -= 0.5 * self.weights[i][j] * state[i] * state[j]
        return e

    def update_stochastic(self, state, temperature, iterations):
        """Stochastic update using temperature-controlled Softmax."""
        current_state = list(state)
        for _ in range(iterations):
            idx = random.randint(0, self.size - 1)
            # Calculate activation for index idx
            activation = sum(self.weights[idx][j] * current_state[j] for j in range(self.size))
            
            # Binary state update probability using Softmax (Logistic function)
            # P(state[idx] = 1) = 1 / (1 + exp(-2 * activation / temperature))
            try:
                prob = 1.0 / (1.0 + math.exp(-2.0 * activation / max(temperature, 1e-5)))
            except OverflowError:
                prob = 1.0 if activation > 0 else 0.0
                
            current_state[idx] = 1 if random.random() < prob else -1
        return current_state
