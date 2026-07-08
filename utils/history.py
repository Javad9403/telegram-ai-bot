import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    import aiosqlite
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False

MAX_HISTORY_TURNS = 20


class HistoryManager:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.backend = None
        self.redis = None
        self.sqlite_conn = None
        self._memory: dict[int, list[dict]] = defaultdict(list)

    async def _ensure_backend(self):
        if self.backend:
            return

        if HAS_REDIS:
            try:
                self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
                await self.redis.ping()
                self.backend = "redis"
                logger.info("History backend: Redis")
                return
            except Exception as e:
                logger.warning("Redis unavailable (%s), falling back", e)

        if HAS_SQLITE:
            self.backend = "sqlite"
            self.sqlite_conn = await aiosqlite.connect("history.db")
            await self.sqlite_conn.execute(
                "CREATE TABLE IF NOT EXISTS history (chat_id INTEGER, role TEXT, content TEXT, idx INTEGER)"
            )
            await self.sqlite_conn.commit()
            logger.info("History backend: SQLite")
            return

        self.backend = "memory"
        logger.info("History backend: In-memory dict")

    def _trim(self, messages: list[dict]) -> list[dict]:
        if len(messages) > MAX_HISTORY_TURNS * 2:
            return messages[-(MAX_HISTORY_TURNS * 2):]
        return messages

    async def add_message(self, chat_id: int, role: str, content: str):
        await self._ensure_backend()

        if self.backend == "redis":
            key = f"history:{chat_id}"
            entry = json.dumps({"role": role, "content": content})
            await self.redis.rpush(key, entry)
            await self.redis.ltrim(key, -(MAX_HISTORY_TURNS * 2), -1)

        elif self.backend == "sqlite" and self.sqlite_conn:
            cursor = await self.sqlite_conn.execute(
                "SELECT COALESCE(MAX(idx), 0) + 1 FROM history WHERE chat_id = ?", (chat_id,)
            )
            row = await cursor.fetchone()
            idx = row[0] if row else 1
            await self.sqlite_conn.execute(
                "INSERT INTO history (chat_id, role, content, idx) VALUES (?, ?, ?, ?)",
                (chat_id, role, content, idx),
            )
            await self.sqlite_conn.commit()
            await self._trim_sqlite(chat_id)

        else:
            self._memory[chat_id].append({"role": role, "content": content})
            self._memory[chat_id] = self._trim(self._memory[chat_id])

    async def _trim_sqlite(self, chat_id: int):
        if not self.sqlite_conn:
            return
        cursor = await self.sqlite_conn.execute(
            "SELECT COUNT(*) FROM history WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        if row and row[0] > MAX_HISTORY_TURNS * 2:
            await self.sqlite_conn.execute(
                "DELETE FROM history WHERE chat_id = ? AND idx <= ("
                "SELECT idx FROM history WHERE chat_id = ? ORDER BY idx ASC LIMIT 1 OFFSET ?"
                ")",
                (chat_id, chat_id, row[0] - MAX_HISTORY_TURNS * 2),
            )
            await self.sqlite_conn.commit()

    async def get_history(self, chat_id: int) -> list[dict]:
        await self._ensure_backend()

        if self.backend == "redis":
            key = f"history:{chat_id}"
            entries = await self.redis.lrange(key, 0, -1)
            return [json.loads(e) for e in entries]

        elif self.backend == "sqlite" and self.sqlite_conn:
            cursor = await self.sqlite_conn.execute(
                "SELECT role, content FROM history WHERE chat_id = ? ORDER BY idx ASC", (chat_id,)
            )
            rows = await cursor.fetchall()
            return [{"role": row[0], "content": row[1]} for row in rows]

        else:
            return self._memory.get(chat_id, [])

    async def clear(self, chat_id: int):
        await self._ensure_backend()

        if self.backend == "redis":
            key = f"history:{chat_id}"
            await self.redis.delete(key)
        elif self.backend == "sqlite" and self.sqlite_conn:
            await self.sqlite_conn.execute("DELETE FROM history WHERE chat_id = ?", (chat_id,))
            await self.sqlite_conn.commit()
        else:
            self._memory.pop(chat_id, None)

    async def close(self):
        if self.redis:
            await self.redis.close()
        if self.sqlite_conn:
            await self.sqlite_conn.close()
