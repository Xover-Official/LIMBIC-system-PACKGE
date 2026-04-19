import grpc
import sys
import os

# Add src to path if package is not installed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from limbic.generated import limbic_pb2, limbic_pb2_grpc

def run():
    # Connect to the Limbic System daemon
    channel = grpc.insecure_channel('localhost:50051')
    stub = limbic_pb2_grpc.LimbicServiceStub(channel)

    # Prepare a stimulus
    stimulus = limbic_pb2.StimulusRequest(
        source="ExternalAgent",
        content="Hello, how are you feeling today?",
        metadata={"type": "greeting", "urgency": 0.1}
    )

    print(f"Injecting stimulus: {stimulus.content}")
    
    try:
        response = stub.InjectStimulus(stimulus)
        print(f"Limbic System response: {response.message}")
    except grpc.RpcError as e:
        print(f"Error connecting to Limbic System: {e}")
        print("Make sure the daemon is running (limbic start)")

if __name__ == "__main__":
    run()
