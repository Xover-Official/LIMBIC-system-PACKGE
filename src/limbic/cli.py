import click
import asyncio
import os
from limbic.daemon import LimbicDaemon

@click.group()
def main():
    """Limbic System CLI"""
    pass

@main.command()
@click.option('--port', default=50051, help='gRPC port')
def start(port):
    """Start the Limbic System daemon"""
    daemon = LimbicDaemon(port=port)
    asyncio.run(daemon.run())

@main.command()
def init():
    """Initialize the Limbic System (DB, etc.)"""
    from limbic.persistence.sqlite_manager import SQLiteManager
    import subprocess
    import sys

    click.echo("Initializing Limbic System...")
    
    # Create necessary directories
    directories = ["data", "config", "docs/images", "examples"]
    for d in directories:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            click.echo(f"Created directory: {d}")

    # Initialize DB
    manager = SQLiteManager()
    try:
        asyncio.run(manager.init_db())
        click.echo("✓ Database initialized in data/limbic.db")
    except Exception as e:
        click.echo(f"❌ Failed to initialize database: {e}")

    # Generate gRPC code
    click.echo("Generating gRPC code from proto...")
    proto_file = "proto/limbic.proto"
    generated_dir = "src/limbic/generated"
    
    if os.path.exists(proto_file):
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            "-I./proto",
            f"--python_out=./{generated_dir}",
            f"--grpc_python_out=./{generated_dir}",
            proto_file
        ]
        try:
            subprocess.run(cmd, check=True)
            click.echo("✓ gRPC code generated.")
            
            # Fix relative import in generated file
            grpc_file = os.path.join(generated_dir, "limbic_pb2_grpc.py")
            if os.path.exists(grpc_file):
                with open(grpc_file, 'r') as f:
                    content = f.read()
                content = content.replace("import limbic_pb2 as limbic__pb2", "from . import limbic_pb2 as limbic__pb2")
                with open(grpc_file, 'w') as f:
                    f.write(content)
                click.echo("✓ gRPC import fixed for package structure.")
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Failed to generate gRPC code: {e}")
        except Exception as e:
            click.echo(f"❌ An error occurred during gRPC generation: {e}")
    else:
        click.echo(f"⚠️ Proto file {proto_file} not found. Skipping gRPC generation.")

    click.echo("Initialization complete.")

if __name__ == "__main__":
    main()
