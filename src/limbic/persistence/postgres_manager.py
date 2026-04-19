import asyncpg
import json
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
from limbic.bus import LimbicBus

logger = logging.getLogger(__name__)

class PostgresManager:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        logger.info(f"Connecting to Postgres at {self.dsn}")
        self.pool = await asyncpg.create_pool(dsn=self.dsn)
        await self.init_db()

    async def init_db(self):
        async with self.pool.acquire() as conn:
            # Events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    topic TEXT,
                    data JSONB,
                    timestamp BIGINT
                )
            """)
            # Social Relationships (Upgraded to Graph-ready)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS social_relationships (
                    actor_id TEXT,
                    target_id TEXT,
                    trust REAL,
                    affinity REAL,
                    debt REAL,
                    interactions INTEGER,
                    last_updated BIGINT,
                    PRIMARY KEY (actor_id, target_id)
                )
            """)
            # Thought Ledger (Immutable)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS thought_ledger (
                    id SERIAL PRIMARY KEY,
                    thought_id TEXT UNIQUE,
                    content JSONB,
                    signature TEXT,
                    signer_id TEXT,
                    timestamp BIGINT
                )
            """)
            # Distributed Lock
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS distributed_locks (
                    lock_name TEXT PRIMARY KEY,
                    owner_id TEXT,
                    expires_at BIGINT
                )
            """)
            # Economic State
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS economic_state (
                    agent_id TEXT PRIMARY KEY,
                    balance REAL,
                    total_spent REAL,
                    last_updated BIGINT
                )
            """)

    async def log_event(self, topic: str, data: Any):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO events (topic, data, timestamp) VALUES ($1, $2, $3)",
                topic, json.dumps(data) if not isinstance(data, str) else data, int(time.time())
            )

    async def update_social_relationship(self, actor_id: str, target_id: str, trust: float, affinity: float, debt: float, interactions: int):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO social_relationships (actor_id, target_id, trust, affinity, debt, interactions, last_updated)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT(actor_id, target_id) DO UPDATE SET
                    trust=excluded.trust,
                    affinity=excluded.affinity,
                    debt=excluded.debt,
                    interactions=excluded.interactions,
                    last_updated=excluded.last_updated
            """, actor_id, target_id, trust, affinity, debt, interactions, int(time.time()))

    async def get_social_relationships(self, actor_id: str):
        if not self.pool: return []
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM social_relationships WHERE actor_id = $1", actor_id)
            return rows

    async def add_thought(self, thought_id: str, content: Any, signature: str, signer_id: str):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO thought_ledger (thought_id, content, signature, signer_id, timestamp)
                VALUES ($1, $2, $3, $4, $5)
            """, thought_id, json.dumps(content) if not isinstance(content, str) else content, signature, signer_id, int(time.time()))

    async def acquire_lock(self, lock_name: str, owner_id: str, ttl: int = 60) -> bool:
        if not self.pool: return False
        async with self.pool.acquire() as conn:
            now = int(time.time())
            await conn.execute("DELETE FROM distributed_locks WHERE lock_name = $1 AND expires_at < $2", lock_name, now)
            try:
                await conn.execute(
                    "INSERT INTO distributed_locks (lock_name, owner_id, expires_at) VALUES ($1, $2, $3)",
                    lock_name, owner_id, now + ttl
                )
                return True
            except asyncpg.UniqueViolationError:
                return False

    async def release_lock(self, lock_name: str, owner_id: str):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM distributed_locks WHERE lock_name = $1 AND owner_id = $2", lock_name, owner_id)

    async def update_economic_state(self, agent_id: str, balance: float, total_spent: float):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO economic_state (agent_id, balance, total_spent, last_updated)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT(agent_id) DO UPDATE SET
                    balance=excluded.balance,
                    total_spent=excluded.total_spent,
                    last_updated=excluded.last_updated
            """, agent_id, balance, total_spent, int(time.time()))

    async def get_economic_state(self, agent_id: str):
        if not self.pool: return None
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM economic_state WHERE agent_id = $1", agent_id)
