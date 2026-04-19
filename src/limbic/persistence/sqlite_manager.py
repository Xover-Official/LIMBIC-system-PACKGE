import aiosqlite
import json
import time
from limbic.bus import LimbicBus

class SQLiteManager:
    def __init__(self, db_path="data/limbic.db"):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    data TEXT,
                    timestamp INTEGER
                )
            """)
            await db.commit()

    async def log_event(self, topic, data):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO events (topic, data, timestamp) VALUES (?, ?, ?)",
                (topic, json.dumps(data), int(time.time()))
            )
            await db.commit()

class EventLogger:
    def __init__(self, bus: LimbicBus, manager: SQLiteManager):
        self.bus = bus
        self.manager = manager
        # Subscribe to everything? Or specific topics
        self.bus.subscribe("STIMULUS", lambda d: asyncio.create_task(self.log("STIMULUS", str(d))))
        self.bus.subscribe("EMOTION_EVOKED", lambda d: asyncio.create_task(self.log("EMOTION_EVOKED", d)))
        self.bus.subscribe("DRIVE_UPDATE", lambda d: asyncio.create_task(self.log("DRIVE_UPDATE", d)))

    async def log(self, topic, data):
        await self.manager.log_event(topic, data)
