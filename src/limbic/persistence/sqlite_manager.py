import aiosqlite
import json
import time
import asyncio
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
            await db.execute("""
                CREATE TABLE IF NOT EXISTS social_relationships (
                    agent_id TEXT PRIMARY KEY,
                    trust REAL,
                    affinity REAL,
                    debt REAL,
                    interactions INTEGER,
                    last_updated INTEGER
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

    async def update_social_relationship(self, agent_id, trust, affinity, debt, interactions):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO social_relationships (agent_id, trust, affinity, debt, interactions, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_id) DO UPDATE SET
                    trust=excluded.trust,
                    affinity=excluded.affinity,
                    debt=excluded.debt,
                    interactions=excluded.interactions,
                    last_updated=excluded.last_updated
            """, (agent_id, trust, affinity, debt, interactions, int(time.time())))
            await db.commit()

    async def get_social_relationships(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM social_relationships") as cursor:
                return await cursor.fetchall()

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
