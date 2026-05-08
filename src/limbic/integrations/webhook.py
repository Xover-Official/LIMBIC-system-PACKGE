import asyncio
import logging
import json
from aiohttp import web
from limbic.bus import LimbicBus
from limbic.generated import limbic_pb2

logger = logging.getLogger(__name__)

class WebhookIntegration:
    def __init__(self, bus: LimbicBus, port: int = 8080):
        self.bus = bus
        self.port = port

    async def handle_stimulus(self, request):
        try:
            data = await request.json()
            source = data.get("source", "webhook")
            content = data.get("content", "")
            metadata = data.get("metadata", {})

            stimulus = limbic_pb2.StimulusRequest(
                source=source,
                content=content,
                metadata=metadata
            )

            await self.bus.publish("STIMULUS", stimulus)
            return web.json_response({"status": "accepted", "message": "Stimulus injected"})
        except Exception as e:
            logger.error(f"Error in webhook stimulus: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=400)

    async def handle_state(self, request):
        # We need a way to get state from the daemon.
        # For now, this is a placeholder or we can use the bus to request state.
        return web.json_response({"message": "Use gRPC for full state streaming. This is a stimulus-only webhook for now."}, status=200)

    async def run(self):
        app = web.Application()
        app.router.add_post('/stimulus', self.handle_stimulus)
        app.router.add_get('/state', self.handle_state)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)

        logger.info(f"Webhook integration starting on port {self.port}...")
        await site.start()

        # Keep alive
        while True:
            await asyncio.sleep(3600)
