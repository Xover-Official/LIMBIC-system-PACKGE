import grpc
import time
import sys
import os

# Add src to path if package is not installed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from limbic.generated import limbic_pb2, limbic_pb2_grpc

def test_emotional_reactions():
    channel = grpc.insecure_channel('localhost:50051')
    stub = limbic_pb2_grpc.LimbicServiceStub(channel)

    stimuli = [
        ("A loud bang behind you!", {"type": "noise", "threat": 0.8}),
        ("Someone gives you a warm hug.", {"type": "social", "valence": 0.7}),
        ("You haven't eaten in 12 hours.", {"type": "physiological", "hunger": 0.9}),
        ("You just won the lottery!", {"type": "reward", "magnitude": 1.0})
    ]

    for content, metadata in stimuli:
        print(f"\n--- Stimulus: {content} ---")
        request = limbic_pb2.StimulusRequest(
            source="EmotionalTester",
            content=content,
            metadata=metadata
        )
        
        try:
            stub.InjectStimulus(request)
            
            # Wait a bit for processing
            time.sleep(1)
            
            # Check state
            state = stub.GetLimbicState(limbic_pb2.Empty())
            print(f"Arousal: {state.arousal:.2f}, Valence: {state.valence:.2f}")
            print(f"Dominant Engine: {state.dominant_engine}")
            print(f"Emotions: {state.emotions}")
            
        except grpc.RpcError as e:
            print(f"RPC Error: {e}")
            break

if __name__ == "__main__":
    test_emotional_reactions()
