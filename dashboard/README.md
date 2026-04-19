# Project Omega Dashboard

This is a Next.js + Tailwind CSS dashboard for real-time monitoring of the Project Omega limbic system.

## Features
- **Real-time Thought Stream**: Smoothly animated thought updates using Framer Motion.
- **Biomimetic Metrics**: Monitoring of Phi-level (Φ), Arousal, Valence, and Ego Coherence.
- **Hormonal Balance**: Visualization of current endocrine levels (Cortisol, Adrenaline, etc.).
- **Existential State**: Tracking of Meaning and Dread.

## Getting Started

1. **Install Dependencies**:
   ```bash
   cd dashboard
   npm install
   ```

2. **Start the Development Server**:
   ```bash
   npm run dev
   ```

3. **Start the WebSocket Proxy**:
   The dashboard requires the WebSocket proxy to be running to receive data from the Limbic Daemon.
   ```bash
   python src/limbic/dashboard/ws_proxy.py
   ```

## Architecture
The dashboard connects to a Python-based WebSocket proxy (`ws_proxy.py`) which translates gRPC streams from the `LimbicDaemon` into WebSocket messages for the React frontend.
