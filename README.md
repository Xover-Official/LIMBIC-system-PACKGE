# LIMBIC-system-PACKGE

Biomimetic Limbic System implementation as a persistent daemon.

## Components

- **Hippocampus v2.0**: Probabilistic Memory Attractor Network.
    - **Dentate Gyrus**: Pattern separation via stochastic noise.
    - **CA3**: Recurrent attractor network with Poisson-distributed update cycles and temperature-controlled state transitions.
    - **CA1**: Probabilistic retrieval and decoding.
    - **Consolidation Engine**: Background memory replay and pruning.
- **Amygdala**: Emotional modulation of memory dynamics. Maps emotional axes (Fear, Seeking) to recall temperature.
- **Hypothalamus**: Homeostatic regulation and system arousal.
- **Stochastic Engine**: Custom implementation of stochastic distributions for environments without high-level math libraries.

## Usage

To start the daemon:

```bash
python3 limbic_daemon.py
```

The system persists its state to `limbic_state.pkl` on exit or periodic saves.
