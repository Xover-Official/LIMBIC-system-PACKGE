import math
import random

class StochasticEngine:
    @staticmethod
    def gaussian(mu=0.0, sigma=1.0):
        """Box-Muller transform for Gaussian noise."""
        u1 = random.random()
        u2 = random.random()
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mu + z0 * sigma

    @staticmethod
    def poisson(lam):
        """Knuth's algorithm for Poisson distribution."""
        if lam <= 0:
            return 0
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= random.random()
        return k - 1

    @staticmethod
    def exponential(lam):
        """Exponential distribution sampler."""
        if lam <= 0:
            return 0
        return -math.log(1.0 - random.random()) / lam

    @staticmethod
    def softmax(vector, temperature=1.0):
        """Softmax sampling from a vector of weights."""
        if temperature <= 0:
            # Argmax if temperature is near zero
            max_val = max(vector)
            indices = [i for i, v in enumerate(vector) if v == max_val]
            return random.choice(indices)
        
        # Shift for numerical stability
        max_v = max(vector)
        exp_vals = [math.exp((v - max_v) / temperature) for v in vector]
        total = sum(exp_vals)
        probs = [ev / total for ev in exp_vals]
        
        # Sample based on probabilities
        r = random.random()
        acc = 0
        for i, p in enumerate(probs):
            acc += p
            if r <= acc:
                return i
        return len(vector) - 1

    @staticmethod
    def add_gaussian_noise(vector, sigma=0.05):
        return [v + StochasticEngine.gaussian(0, sigma) for v in vector]
