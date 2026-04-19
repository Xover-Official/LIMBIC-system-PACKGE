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
    # TODO: Implement DB initialization
    click.echo("Initializing Limbic System...")
    os.makedirs("data", exist_ok=True)
    click.echo("Done.")

if __name__ == "__main__":
    main()
