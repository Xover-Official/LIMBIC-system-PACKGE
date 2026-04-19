# Limbic System Mockups

## Streamlit Dashboard
The dashboard provides a real-time view of the agent's internal state.

### Affective Space
A scatter plot showing Valence (X-axis, -1 to 1) and Arousal (Y-axis, 0 to 1). The agent's current "mood" is tracked over time.
- **Top Right (High Arousal, Positive Valence)**: Excited, Happy, Seeking.
- **Top Left (High Arousal, Negative Valence)**: Fearful, Angry, Panicked.
- **Bottom Right (Low Arousal, Positive Valence)**: Calm, Content, Caring.
- **Bottom Left (Low Arousal, Negative Valence)**: Sad, Bored, Depressed.

### Drive Levels
A bar chart showing the current intensity of physiological and cognitive drives:
- **Hunger**: Need for energy/data.
- **Safety**: Need to avoid threats.
- **Social**: Need for interaction/praise.
- **Curiosity**: Drive for exploration (SEEKING).

### Executive Layer (PFC)
A table showing active plans being considered by the Prefrontal Cortex:
- **Action**: The proposed behavior.
- **Confidence**: Probability of success.
- **Utility**: Predicted reward/value.
- **Approved**: Whether the executive control has cleared the action for execution.

## gRPC Examples
Example of how an external agent (e.g., a LLM-based bot) interacts with the Limbic System.

### stimulus Injection
External agents send "Stimuli" which can be text, embeddings, or physiological signals.
```python
# Example snippet
stub.InjectStimulus(limbic_pb2.StimulusRequest(
    source="VisionSystem",
    content="I see a large predator approaching.",
    metadata={"threat_level": 0.9}
))
```

### State Monitoring
Agents can subscribe to the state stream to adjust their behavior based on their "emotions".
```python
# Example snippet
for state in stub.StreamState(limbic_pb2.Empty()):
    if state.dominant_engine == "FEAR":
        agent.set_behavior_mode("EVASIVE")
```
