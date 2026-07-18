import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from config import config

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    status: str = TaskStatus.PENDING.value
    priority: int = Priority.MEDIUM.value
    due_date: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)


@dataclass
class Note:
    id: str
    title: str
    content: str
    tags: list[str]
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        return cls(**data)


@dataclass
class Reminder:
    id: str
    title: str
    message: str
    remind_at: str
    recurring: bool = False
    recurrence_pattern: Optional[str] = None
    is_active: bool = True
    created_at: str = ""
    last_triggered: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Reminder":
        return cls(**data)


@dataclass
class CalendarEvent:
    id: str
    title: str
    description: str = ""
    start_time: str = ""
    end_time: Optional[str] = None
    location: Optional[str] = None
    is_all_day: bool = False
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CalendarEvent":
        return cls(**data)


class SecretaryManager:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None
        self._memory_tasks: dict[int, dict[str, Task]] = {}
        self._memory_notes: dict[int, dict[str, Note]] = {}
        self._memory_reminders: dict[int, dict[str, Reminder]] = {}
        self._memory_events: dict[int, dict[str, CalendarEvent]] = {}

    async def _ensure_redis(self):
        if self.redis:
            return
        if HAS_REDIS:
            try:
                self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
                await self.redis.ping()
                logger.info("Secretary backend: Redis")
                return
            except Exception as e:
                logger.warning("Redis unavailable for secretary (%s), using memory", e)
        logger.info("Secretary backend: In-memory dict")

    def _task_key(self, chat_id: int) -> str:
        return f"secretary:tasks:{chat_id}"

    def _note_key(self, chat_id: int) -> str:
        return f"secretary:notes:{chat_id}"

    def _reminder_key(self, chat_id: int) -> str:
        return f"secretary:reminders:{chat_id}"

    def _event_key(self, chat_id: int) -> str:
        return f"secretary:events:{chat_id}"

    def _generate_id(self) -> str:
        return datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

    # ========== TASKS ==========
    async def add_task(
        self,
        chat_id: int,
        title: str,
        description: str = "",
        priority: int = Priority.MEDIUM.value,
        due_date: Optional[str] = None,
    ) -> Task:
        await self._ensure_redis()
        task = Task(
            id=self._generate_id(),
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        if self.redis:
            key = self._task_key(chat_id)
            await self.redis.hset(key, task.id, json.dumps(task.to_dict()))
        else:
            self._memory_tasks.setdefault(chat_id, {})[task.id] = task
        return task

    async def get_task(self, chat_id: int, task_id: str) -> Optional[Task]:
        await self._ensure_redis()
        if self.redis:
            key = self._task_key(chat_id)
            data = await self.redis.hget(key, task_id)
            return Task.from_dict(json.loads(data)) if data else None
        return self._memory_tasks.get(chat_id, {}).get(task_id)

    async def get_tasks(
        self,
        chat_id: int,
        status: Optional[str] = None,
    ) -> list[Task]:
        await self._ensure_redis()
        tasks = []
        if self.redis:
            key = self._task_key(chat_id)
            data = await self.redis.hgetall(key)
            for v in data.values():
                task = Task.from_dict(json.loads(v))
                if status is None or task.status == status:
                    tasks.append(task)
        else:
            for task in self._memory_tasks.get(chat_id, {}).values():
                if status is None or task.status == status:
                    tasks.append(task)
        tasks.sort(key=lambda t: (t.priority * -1, t.due_date or "zzzz"))
        return tasks

    async def update_task(
        self,
        chat_id: int,
        task_id: str,
        **kwargs,
    ) -> Optional[Task]:
        task = await self.get_task(chat_id, task_id)
        if not task:
            return None
        for k, v in kwargs.items():
            if hasattr(task, k):
                setattr(task, k, v)
        task.updated_at = datetime.now().isoformat()
        if task.status == TaskStatus.DONE.value and not task.completed_at:
            task.completed_at = datetime.now().isoformat()
        if self.redis:
            key = self._task_key(chat_id)
            await self.redis.hset(key, task.id, json.dumps(task.to_dict()))
        else:
            self._memory_tasks[chat_id][task.id] = task
        return task

    async def delete_task(self, chat_id: int, task_id: str) -> bool:
        await self._ensure_redis()
        if self.redis:
            key = self._task_key(chat_id)
            return await self.redis.hdel(key, task_id) > 0
        return self._memory_tasks.get(chat_id, {}).pop(task_id, None) is not None

    # ========== NOTES ==========
    async def add_note(
        self,
        chat_id: int,
        title: str,
        content: str,
        tags: list[str] = None,
    ) -> Note:
        await self._ensure_redis()
        note = Note(
            id=self._generate_id(),
            title=title,
            content=content,
            tags=tags or [],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        if self.redis:
            key = self._note_key(chat_id)
            await self.redis.hset(key, note.id, json.dumps(note.to_dict()))
        else:
            self._memory_notes.setdefault(chat_id, {})[note.id] = note
        return note

    async def get_note(self, chat_id: int, note_id: str) -> Optional[Note]:
        await self._ensure_redis()
        if self.redis:
            key = self._note_key(chat_id)
            data = await self.redis.hget(key, note_id)
            return Note.from_dict(json.loads(data)) if data else None
        return self._memory_notes.get(chat_id, {}).get(note_id)

    async def get_notes(self, chat_id: int, tag: Optional[str] = None) -> list[Note]:
        await self._ensure_redis()
        notes = []
        if self.redis:
            key = self._note_key(chat_id)
            data = await self.redis.hgetall(key)
            for v in data.values():
                note = Note.from_dict(json.loads(v))
                if tag is None or tag in note.tags:
                    notes.append(note)
        else:
            for note in self._memory_notes.get(chat_id, {}).values():
                if tag is None or tag in note.tags:
                    notes.append(note)
        notes.sort(key=lambda n: n.updated_at, reverse=True)
        return notes

    async def update_note(
        self,
        chat_id: int,
        note_id: str,
        **kwargs,
    ) -> Optional[Note]:
        note = await self.get_note(chat_id, note_id)
        if not note:
            return None
        for k, v in kwargs.items():
            if hasattr(note, k):
                setattr(note, k, v)
        note.updated_at = datetime.now().isoformat()
        if self.redis:
            key = self._note_key(chat_id)
            await self.redis.hset(key, note.id, json.dumps(note.to_dict()))
        else:
            self._memory_notes[chat_id][note.id] = note
        return note

    async def delete_note(self, chat_id: int, note_id: str) -> bool:
        await self._ensure_redis()
        if self.redis:
            key = self._note_key(chat_id)
            return await self.redis.hdel(key, note_id) > 0
        return self._memory_notes.get(chat_id, {}).pop(note_id, None) is not None

    # ========== REMINDERS ==========
    async def add_reminder(
        self,
        chat_id: int,
        title: str,
        message: str,
        remind_at: str,
        recurring: bool = False,
        recurrence_pattern: Optional[str] = None,
    ) -> Reminder:
        await self._ensure_redis()
        reminder = Reminder(
            id=self._generate_id(),
            title=title,
            message=message,
            remind_at=remind_at,
            recurring=recurring,
            recurrence_pattern=recurrence_pattern,
            created_at=datetime.now().isoformat(),
        )
        if self.redis:
            key = self._reminder_key(chat_id)
            await self.redis.hset(key, reminder.id, json.dumps(reminder.to_dict()))
        else:
            self._memory_reminders.setdefault(chat_id, {})[reminder.id] = reminder
        return reminder

    async def get_reminder(self, chat_id: int, reminder_id: str) -> Optional[Reminder]:
        await self._ensure_redis()
        if self.redis:
            key = self._reminder_key(chat_id)
            data = await self.redis.hget(key, reminder_id)
            return Reminder.from_dict(json.loads(data)) if data else None
        return self._memory_reminders.get(chat_id, {}).get(reminder_id)

    async def get_reminders(
        self,
        chat_id: int,
        active_only: bool = True,
        before: Optional[str] = None,
    ) -> list[Reminder]:
        await self._ensure_redis()
        reminders = []
        if self.redis:
            key = self._reminder_key(chat_id)
            data = await self.redis.hgetall(key)
            for v in data.values():
                r = Reminder.from_dict(json.loads(v))
                if active_only and not r.is_active:
                    continue
                if before and r.remind_at > before:
                    continue
                reminders.append(r)
        else:
            for r in self._memory_reminders.get(chat_id, {}).values():
                if active_only and not r.is_active:
                    continue
                if before and r.remind_at > before:
                    continue
                reminders.append(r)
        reminders.sort(key=lambda x: x.remind_at)
        return reminders

    async def update_reminder(
        self,
        chat_id: int,
        reminder_id: str,
        **kwargs,
    ) -> Optional[Reminder]:
        reminder = await self.get_reminder(chat_id, reminder_id)
        if not reminder:
            return None
        for k, v in kwargs.items():
            if hasattr(reminder, k):
                setattr(reminder, k, v)
        if self.redis:
            key = self._reminder_key(chat_id)
            await self.redis.hset(key, reminder.id, json.dumps(reminder.to_dict()))
        else:
            self._memory_reminders[chat_id][reminder.id] = reminder
        return reminder

    async def delete_reminder(self, chat_id: int, reminder_id: str) -> bool:
        await self._ensure_redis()
        if self.redis:
            key = self._reminder_key(chat_id)
            return await self.redis.hdel(key, reminder_id) > 0
        return self._memory_reminders.get(chat_id, {}).pop(reminder_id, None) is not None

    # ========== CALENDAR EVENTS ==========
    async def add_event(
        self,
        chat_id: int,
        title: str,
        start_time: str,
        description: str = "",
        end_time: Optional[str] = None,
        location: Optional[str] = None,
        is_all_day: bool = False,
    ) -> CalendarEvent:
        await self._ensure_redis()
        event = CalendarEvent(
            id=self._generate_id(),
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location,
            is_all_day=is_all_day,
            created_at=datetime.now().isoformat(),
        )
        if self.redis:
            key = self._event_key(chat_id)
            await self.redis.hset(key, event.id, json.dumps(event.to_dict()))
        else:
            self._memory_events.setdefault(chat_id, {})[event.id] = event
        return event

    async def get_event(self, chat_id: int, event_id: str) -> Optional[CalendarEvent]:
        await self._ensure_redis()
        if self.redis:
            key = self._event_key(chat_id)
            data = await self.redis.hget(key, event_id)
            return CalendarEvent.from_dict(json.loads(data)) if data else None
        return self._memory_events.get(chat_id, {}).get(event_id)

    async def get_events(
        self,
        chat_id: int,
        start_from: Optional[str] = None,
        end_before: Optional[str] = None,
    ) -> list[CalendarEvent]:
        await self._ensure_redis()
        events = []
        if self.redis:
            key = self._event_key(chat_id)
            data = await self.redis.hgetall(key)
            for v in data.values():
                e = CalendarEvent.from_dict(json.loads(v))
                if start_from and e.start_time < start_from:
                    continue
                if end_before and e.start_time > end_before:
                    continue
                events.append(e)
        else:
            for e in self._memory_events.get(chat_id, {}).values():
                if start_from and e.start_time < start_from:
                    continue
                if end_before and e.start_time > end_before:
                    continue
                events.append(e)
        events.sort(key=lambda x: x.start_time)
        return events

    async def update_event(
        self,
        chat_id: int,
        event_id: str,
        **kwargs,
    ) -> Optional[CalendarEvent]:
        event = await self.get_event(chat_id, event_id)
        if not event:
            return None
        for k, v in kwargs.items():
            if hasattr(event, k):
                setattr(event, k, v)
        if self.redis:
            key = self._event_key(chat_id)
            await self.redis.hset(key, event.id, json.dumps(event.to_dict()))
        else:
            self._memory_events[chat_id][event.id] = event
        return event

    async def delete_event(self, chat_id: int, event_id: str) -> bool:
        await self._ensure_redis()
        if self.redis:
            key = self._event_key(chat_id)
            return await self.redis.hdel(key, event_id) > 0
        return self._memory_events.get(chat_id, {}).pop(event_id, None) is not None

    # ========== SUMMARY ==========
    async def get_daily_summary(self, chat_id: int, date: Optional[str] = None) -> str:
        """Generate a daily summary of tasks, events, reminders."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        date_start = f"{date}T00:00:00"
        date_end = f"{date}T23:59:59"

        tasks = await self.get_tasks(chat_id)
        pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING.value and t.due_date and t.due_date.startswith(date)]

        events = await self.get_events(chat_id, start_from=date_start, end_before=date_end)
        reminders = await self.get_reminders(chat_id, active_only=True, before=date_end)

        lines = [f"📋 <b>خلاصه روز {date}</b>\n"]

        if pending_tasks:
            lines.append("📝 <b>تسک‌های امروز:</b>")
            for t in pending_tasks:
                p_icon = "🔴" if t.priority >= 3 else "🟡" if t.priority == 2 else "🟢"
                lines.append(f"  {p_icon} {t.title} ({t.due_date[11:16] if t.due_date else 'بدون زمان'})")
        else:
            lines.append("📝 <b>تسک‌های امروز:</b> هیچ‌کدام")

        if events:
            lines.append("\n📅 <b>رویدادهای امروز:</b>")
            for e in events:
                lines.append(f"  🕐 {e.start_time[11:16]} - {e.title}")
        else:
            lines.append("\n📅 <b>رویدادهای امروز:</b> هیچ‌کدام")

        if reminders:
            lines.append("\n⏰ <b>یادآوری‌های فعال:</b>")
            for r in reminders:
                lines.append(f"  ⏰ {r.remind_at[11:16]} - {r.title}")
        else:
            lines.append("\n⏰ <b>یادآوری‌های فعال:</b> هیچ‌کدام")

        return "\n".join(lines)

    async def get_weekly_summary(self, chat_id: int, start_date: Optional[str] = None) -> str:
        """Generate a weekly summary."""
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")
        start_dt = datetime.fromisoformat(start_date)
        end_dt = start_dt + timedelta(days=7)
        end_date = end_dt.strftime("%Y-%m-%d")

        tasks = await self.get_tasks(chat_id)
        pending_tasks = [
            t for t in tasks
            if t.status == TaskStatus.PENDING.value and t.due_date and start_date <= t.due_date[:10] <= end_date
        ]

        events = await self.get_events(chat_id, start_from=f"{start_date}T00:00:00", end_before=f"{end_date}T23:59:59")

        lines = [f"📋 <b>خلاصه هفته {start_date} تا {end_date}</b>\n"]

        if pending_tasks:
            lines.append("📝 <b>تسک‌های این هفته:</b>")
            for t in pending_tasks:
                p_icon = "🔴" if t.priority >= 3 else "🟡" if t.priority == 2 else "🟢"
                lines.append(f"  {p_icon} {t.title} ({t.due_date[:10] if t.due_date else 'بدون تاریخ'})")
        else:
            lines.append("📝 <b>تسک‌های این هفته:</b> هیچ‌کدام")

        if events:
            lines.append("\n📅 <b>رویدادهای این هفته:</b>")
            for e in events:
                lines.append(f"  🕐 {e.start_time[:10]} {e.start_time[11:16]} - {e.title}")
        else:
            lines.append("\n📅 <b>رویدادهای این هفته:</b> هیچ‌کدام")

        return "\n".join(lines)