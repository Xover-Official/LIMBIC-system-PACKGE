# Limbic System Package

A biomimetic Limbic System for autonomous AI agents, implemented as a persistent Python daemon.

## Features
- **gRPC Interface**: High-performance external communication.
- **Asyncio Message Bus**: Decoupled internal module communication.
- **Biomimetic Modules**:
    - **Hypothalamus**: Drive management (Hunger, Safety, etc.).
    - **Amygdala**: Fast-path significance evaluation.
    - **Hippocampus**: Associative memory using FAISS.
    - **Nucleus Accumbens**: Reward prediction error and dopamine modulation.
    - **Insula**: Interoception and feeling generation.
- **Pankseppian Emotion Engines**: SEEKING, FEAR, PANIC, CARE.

## Installation
```bash
pip install -e .
```

## Usage
1. Initialize the system:
   ```bash
   limbic init
   ```
2. Start the daemon:
   ```bash
   limbic start
   ```

## Architecture
The system uses an internal `LimbicBus` to pass messages between modules. For example, a `STIMULUS` message from gRPC is picked up by the Amygdala, Hippocampus, and Hypothalamus. The Amygdala might then trigger an `EMOTION_EVOKED` event, which the relevant Emotion Engine (e.g., FEAR) responds to by increasing its activation level.
