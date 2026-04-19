import grpc
import sys
import os

# Add src to path if package is not installed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from limbic.generated import limbic_pb2, limbic_pb2_grpc

def stream_consciousness():
    channel = grpc.insecure_channel('localhost:50051')
    stub = limbic_pb2_grpc.LimbicServiceStub(channel)

    print("Listening to Limbic System consciousness broadcast...")
    print("Press Ctrl+C to stop.\n")

    try:
        for state in stub.StreamState(limbic_pb2.Empty()):
            c = state.consciousness
            print(f"[{state.timestamp}] Focus: {c.current_focus} (Salience: {c.focus_salience:.2f})")
            if c.self_narrative:
                print(f"Narrative: {c.self_narrative}")
            print(f"Drives: {state.drives}")
            print("-" * 40)
    except grpc.RpcError as e:
        print(f"RPC Error: {e}")
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    stream_consciousness()
