import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender

from utils.filters import ChatTypeFilter, OwnerFilter
from utils.secretary import (
    SecretaryManager,
    Task,
    Note,
    Reminder,
    CalendarEvent,
    TaskStatus,
    Priority,
)
from handlers.keyboards import get_main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)

SECRETARY_TRIGGERS = {
    "remind": [
        r"یادآوری\s+کن",
        r"یاد\s*آوری",
        r"به\s+یاد\s+بیاور",
        r"یادم\s+بگو",
        r"یادآور",
        r"remind",
        r"set\s+reminder",
    ],
    "task": [
        r"تسک\s+(جدید|اضافه|ایجاد)",
        r"کار\s+(جدید|اضافه)",
        r"وظیفه\s+(جدید|اضافه)",
        r"task\s+add",
        r"add\s+task",
        r"todo",
        r"تو\s*دو",
    ],
    "note": [
        r"یادداشت",
        r"نوت",
        r"note",
        r"یادداشت\s+nieuw",
        r"ذخیره\s+کن",
    ],
    "calendar": [
        r"تقویم",
        r"رویداد\s+(جدید|اضافه)",
        r"جلسه\s+(جدید|تعیین)",
        r"calendar",
        r"event",
        r"meeting",
    ],
    "summary": [
        r"خلاصه",
        r"گزارش",
        r"summary",
        r"روزانه",
        r"هفته",
    ],
}

PERSIAN_MONTHS = {
    "فروردین": 1, "اردیبهشت": 2, "خرداد": 3,
    "تیر": 4, "مرداد": 5, "شهریور": 6,
    "مهر": 7, "آبان": 8, "آذر": 9,
    "دی": 10, "بهمن": 11, "اسفند": 12,
}

PERSIAN_DAYS = {
    "شنبه": 0, "یکشنبه": 1, "دوشنبه": 2, "سه‌شنبه": 3,
    "چهارشنبه": 4, "پنج‌شنبه": 5, "جمعه": 6,
}

RELATIVE_DATES = {
    "امروز": 0,
    "فردا": 1,
    "پرس فردا": 2,
    "هفته بعد": 7,
    "ماه بعد": 30,
}


def parse_persian_datetime(text: str) -> Optional[datetime]:
    """Parse Persian natural language datetime expressions."""
    text = text.strip().lower()
    now = datetime.now()

    for rel, days in RELATIVE_DATES.items():
        if rel in text:
            base = now + timedelta(days=days)
            time_match = re.search(r"ساعت\s*(\d{1,2})[:.:]?(\d{2})?", text)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                return base.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return base.replace(hour=9, minute=0, second=0, microsecond=0)

    time_match = re.search(r"(\d{1,2})[:.:](\d{2})", text)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return None


def extract_secretary_command(text: str) -> Optional[tuple[str, str]]:
    """Extract secretary command type and content from natural language."""
    text_lower = text.lower().strip()

    for cmd_type, patterns in SECRETARY_TRIGGERS.items():
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                content = text[match.end():].strip()
                content = re.sub(r"^[:\-،\s]+", "", content)
                return cmd_type, content

    return None


async def _process_secretary_message(
    message: Message,
    secretary: SecretaryManager,
    text: str,
    chat_id: int,
):
    """Process a message as a secretary command."""
    extracted = extract_secretary_command(text)
    if not extracted:
        return False

    cmd_type, content = extracted

    if cmd_type == "remind":
        return await _handle_natural_remind(message, secretary, content, chat_id)
    elif cmd_type == "task":
        return await _handle_natural_task(message, secretary, content, chat_id)
    elif cmd_type == "note":
        return await _handle_natural_note(message, secretary, content, chat_id)
    elif cmd_type == "calendar":
        return await _handle_natural_calendar(message, secretary, content, chat_id)
    elif cmd_type == "summary":
        return await _handle_natural_summary(message, secretary, content, chat_id)

    return False


async def _handle_natural_remind(
    message: Message,
    secretary: SecretaryManager,
    content: str,
    chat_id: int,
):
    """Handle natural language reminder."""
    dt = parse_persian_datetime(content)
    if not dt:
        await message.answer(
            "⏰ لطفاً زمان رو مشخص کن:\n"
            "مثال: «یادآوری کن فردا ساعت ۱۴:۳۰ جلسه دارم»\n"
            "یا: «یادم بگو امروز ساعت ۵ عصر خرید کنم»"
        )
        return True

    title_match = re.search(r"(جلسه|خریده?|تماس|ملاقات|کار|درس|ورزش|دوا|دواء)\s*(.*)", content)
    title = title_match.group(0) if title_match else content[:50]

    reminder = await secretary.add_reminder(
        chat_id=chat_id,
        title=title.strip(),
        message=content,
        remind_at=dt.isoformat(),
    )

    await message.answer(
        f"✅ <b>یادآوری ثبت شد</b>\n\n"
        f"⏰ <b>زمان:</b> {dt.strftime('%Y-%m-%d %H:%M')}\n"
        f"📝 <b>موضوع:</b> {title.strip()}\n\n"
        f"آی‌دی: <code>{reminder.id}</code>",
        parse_mode="HTML",
    )
    return True


async def _handle_natural_task(
    message: Message,
    secretary: SecretaryManager,
    content: str,
    chat_id: int,
):
    """Handle natural language task."""
    dt = parse_persian_datetime(content)
    due_date = dt.isoformat() if dt else None

    priority = Priority.MEDIUM.value
    if any(w in content for w in ["فوری", "اضطراری", "acil", "urgent", "مهم"]):
        priority = Priority.HIGH.value
    elif any(w in content for w in ["کم", "low", "بعداً"]):
        priority = Priority.LOW.value

    task = await secretary.add_task(
        chat_id=chat_id,
        title=content[:80],
        description=content,
        priority=priority,
        due_date=due_date,
    )

    due_str = f"📅 {dt.strftime('%Y-%m-%d %H:%M')}" if dt else "بدون تاریخ"
    p_icon = "🔴" if priority >= 3 else "🟡" if priority == 2 else "🟢"

    await message.answer(
        f"✅ <b>تسک اضافه شد</b>\n\n"
        f"{p_icon} <b>اولویت:</b> {'بالا' if priority >= 3 else 'متوسط' if priority == 2 else 'پایین'}\n"
        f"📝 <b>عنوان:</b> {task.title}\n"
        f"{due_str}\n\n"
        f"آی‌دی: <code>{task.id}</code>",
        parse_mode="HTML",
    )
    return True


async def _handle_natural_note(
    message: Message,
    secretary: SecretaryManager,
    content: str,
    chat_id: int,
):
    """Handle natural language note."""
    if not content.strip():
        await message.answer("📝 چی بنویسم توی یادداشت؟ متن رو بفرست.")
        return True

    note = await secretary.add_note(
        chat_id=chat_id,
        title=content[:50],
        content=content,
    )

    await message.answer(
        f"📝 <b>یادداشت ذخیره شد</b>\n\n"
        f"📄 {note.content[:200]}{'...' if len(note.content) > 200 else ''}\n\n"
        f"آی‌دی: <code>{note.id}</code>",
        parse_mode="HTML",
    )
    return True


async def _handle_natural_calendar(
    message: Message,
    secretary: SecretaryManager,
    content: str,
    chat_id: int,
):
    """Handle natural language calendar event."""
    dt = parse_persian_datetime(content)
    if not dt:
        await message.answer(
            "📅 لطفاً زمان رویداد رو مشخص کن:\n"
            "مثال: «جلسه فردا ساعت ۱۰» یا «رویداد جدید هفته بعد ساعت ۱۴»"
        )
        return True

    end_dt = dt + timedelta(hours=1)

    event = await secretary.add_event(
        chat_id=chat_id,
        title=content[:80],
        start_time=dt.isoformat(),
        end_time=end_dt.isoformat(),
    )

    await message.answer(
        f"📅 <b>رویداد تقویم ثبت شد</b>\n\n"
        f"🕐 <b>شروع:</b> {dt.strftime('%Y-%m-%d %H:%M')}\n"
        f"🕑 <b>پایان:</b> {end_dt.strftime('%H:%M')}\n"
        f"📝 <b>عنوان:</b> {event.title}\n\n"
        f"آی‌دی: <code>{event.id}</code>",
        parse_mode="HTML",
    )
    return True


async def _handle_natural_summary(
    message: Message,
    secretary: SecretaryManager,
    content: str,
    chat_id: int,
):
    """Handle natural language summary request."""
    if "هفته" in content or "weekly" in content.lower():
        summary = await secretary.get_weekly_summary(chat_id)
    else:
        summary = await secretary.get_daily_summary(chat_id)

    await message.answer(summary, parse_mode="HTML")
    return True


# ========== COMMAND HANDLERS ==========

@router.message(Command("remind"))
async def cmd_remind(message: Message, secretary: SecretaryManager):
    """Set a reminder: /remind [time] [text]"""
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            "⏰ <b>فرمت:</b> <code>/remind [زمان] [متن]</code>\n\n"
            "<b>مثال‌ها:</b>\n"
            "• <code>/remind 14:30 جلسه با تیم</code>\n"
            "• <code>/remind فردا ۰۹:۰۰ خرید شیر</code>\n"
            "• <code>/remind ۲۰۲۴-۱۲-۲۵ ۱۰:۰۰ کریسمس</code>",
            parse_mode="HTML",
        )
        return

    time_str = args[1]
    text = args[2] if len(args) > 2 else ""

    dt = parse_persian_datetime(time_str)
    if not dt:
        try:
            dt = datetime.fromisoformat(time_str)
        except ValueError:
            await message.answer("❌ فرمت زمان نامعتبر. از فرمت HH:MM یا 'فردا ۱۴:۳۰' استفاده کن.")
            return

    reminder = await secretary.add_reminder(
        chat_id=message.chat.id,
        title=text[:50],
        message=text,
        remind_at=dt.isoformat(),
    )

    await message.answer(
        f"✅ <b>یادآوری ثبت شد</b>\n\n"
        f"⏰ <b>زمان:</b> {dt.strftime('%Y-%m-%d %H:%M')}\n"
        f"📝 <b>پیام:</b> {text}\n\n"
        f"آی‌دی: <code>{reminder.id}</code>",
        parse_mode="HTML",
    )


@router.message(Command("task"))
async def cmd_task(message: Message, secretary: SecretaryManager):
    """Add task: /task add [text] | /task list | /task done [id]"""
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.answer(
            "📋 <b>مدیریت تسک‌ها:</b>\n\n"
            "• <code>/task add عنوان تسک</code> - تسک جدید\n"
            "• <code>/task list</code> - لیست تسک‌ها\n"
            "• <code>/task done آیدی</code> - تکمیل تسک\n"
            "• <code>/task del آیدی</code> - حذف تسک\n"
            "• <code>/task pending</code> - فقط تسک‌های در انتظار",
            parse_mode="HTML",
        )
        return

    subcmd = args[1].lower()

    if subcmd == "add":
        if len(args) < 3:
            await message.answer("❌ متن تسک رو بنویس: <code>/task add خرید شیر</code>", parse_mode="HTML")
            return
        text = args[2]
        dt = parse_persian_datetime(text)
        priority = Priority.MEDIUM.value
        if "فوری" in text or "مهم" in text:
            priority = Priority.HIGH.value

        task = await secretary.add_task(
            chat_id=message.chat.id,
            title=text[:80],
            description=text,
            priority=priority,
            due_date=dt.isoformat() if dt else None,
        )
        due_str = f"📅 {dt.strftime('%Y-%m-%d %H:%M')}" if dt else "بدون تاریخ"
        p_icon = "🔴" if priority >= 3 else "🟡" if priority == 2 else "🟢"
        await message.answer(
            f"✅ <b>تسک اضافه شد</b>\n\n"
            f"{p_icon} <b>اولویت:</b> {'بالا' if priority >= 3 else 'متوسط'}\n"
            f"📝 <b>عنوان:</b> {task.title}\n"
            f"{due_str}\n\n"
            f"آی‌دی: <code>{task.id}</code>",
            parse_mode="HTML",
        )

    elif subcmd in ("list", "pending"):
        status = TaskStatus.PENDING.value if subcmd == "pending" else None
        tasks = await secretary.get_tasks(message.chat.id, status=status)
        if not tasks:
            await message.answer("📭 هیچ تسکی پیدا نشد.")
            return

        lines = ["📋 <b>لیست تسک‌ها:</b>\n"]
        for t in tasks[:20]:
            p_icon = "🔴" if t.priority >= 3 else "🟡" if t.priority == 2 else "🟢"
            status_icon = "✅" if t.status == TaskStatus.DONE.value else "⏳" if t.status == TaskStatus.IN_PROGRESS.value else "🔵"
            due = f" 📅 {t.due_date[:16]}" if t.due_date else ""
            lines.append(f"{status_icon} {p_icon} <code>{t.id[:8]}</code> {t.title}{due}")

        if len(tasks) > 20:
            lines.append(f"\n... و {len(tasks) - 20} تسک دیگر")
        await message.answer("\n".join(lines), parse_mode="HTML")

    elif subcmd == "done":
        if len(args) < 3:
            await message.answer("❌ آیدی تسک رو بده: <code>/task done آیدی</code>", parse_mode="HTML")
            return
        task_id = args[2]
        updated = await secretary.update_task(message.chat.id, task_id, status=TaskStatus.DONE.value)
        if updated:
            await message.answer(f"✅ تسک <code>{task_id}</code> تکمیل شد!", parse_mode="HTML")
        else:
            await message.answer("❌ تسک پیدا نشد.")

    elif subcmd == "del":
        if len(args) < 3:
            await message.answer("❌ آیدی تسک رو بده: <code>/task del آیدی</code>", parse_mode="HTML")
            return
        task_id = args[2]
        deleted = await secretary.delete_task(message.chat.id, task_id)
        if deleted:
            await message.answer(f"🗑️ تسک <code>{task_id}</code> حذف شد.", parse_mode="HTML")
        else:
            await message.answer("❌ تسک پیدا نشد.")

    else:
        await message.answer("❌ دستور ناشناس. از <code>/task</code> برای راهنما استفاده کن.", parse_mode="HTML")


@router.message(Command("tasks"))
async def cmd_tasks(message: Message, secretary: SecretaryManager):
    """Show all tasks."""
    tasks = await secretary.get_tasks(message.chat.id)
    if not tasks:
        await message.answer("📭 هیچ تسکی ثبت نشده. با <code>/task add</code> یکی اضافه کن.", parse_mode="HTML")
        return

    lines = ["📋 <b>تمام تسک‌ها:</b>\n"]
    for t in tasks:
        p_icon = "🔴" if t.priority >= 3 else "🟡" if t.priority == 2 else "🟢"
        status_icon = "✅" if t.status == TaskStatus.DONE.value else "⏳" if t.status == TaskStatus.IN_PROGRESS.value else "🔵"
        due = f" 📅 {t.due_date[:16]}" if t.due_date else ""
        lines.append(f"{status_icon} {p_icon} <code>{t.id[:8]}</code> {t.title}{due}")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("note"))
async def cmd_note(message: Message, secretary: SecretaryManager):
    """Quick note: /note [text]"""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "📝 <b>یادداشت سریع:</b> <code>/note متن یادداشت</code>\n"
            "یا فقط بنویس: «یادداشت: این یه نکته مهمه»",
            parse_mode="HTML",
        )
        return

    content = args[1]
    note = await secretary.add_note(
        chat_id=message.chat.id,
        title=content[:50],
        content=content,
    )

    await message.answer(
        f"📝 <b>یادداشت ذخیره شد</b>\n\n"
        f"📄 {note.content[:200]}{'...' if len(note.content) > 200 else ''}\n\n"
        f"آی‌دی: <code>{note.id}</code>",
        parse_mode="HTML",
    )


@router.message(Command("notes"))
async def cmd_notes(message: Message, secretary: SecretaryManager):
    """Show all notes."""
    notes = await secretary.get_notes(message.chat.id)
    if not notes:
        await message.answer("📭 هیچ یادداشتی نیست. با <code>/note</code> یکی بساز.", parse_mode="HTML")
        return

    lines = ["📝 <b>یادداشت‌ها:</b>\n"]
    for n in notes[:15]:
        lines.append(f"📄 <code>{n.id[:8]}</code> {n.title}")
        if n.content != n.title:
            lines.append(f"   {n.content[:100]}{'...' if len(n.content) > 100 else ''}")

    if len(notes) > 15:
        lines.append(f"\n... و {len(notes) - 15} یادداشت دیگر")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("calendar"))
async def cmd_calendar(message: Message, secretary: SecretaryManager):
    """Show calendar events: /calendar [today|week]"""
    args = message.text.split(maxsplit=1)
    period = args[1].lower() if len(args) > 1 else "today"

    now = datetime.now()
    if period == "week":
        start = now.strftime("%Y-%m-%d")
        end = (now + timedelta(days=7)).strftime("%Y-%m-%d")
        events = await secretary.get_events(message.chat.id, start_from=f"{start}T00:00:00", end_before=f"{end}T23:59:59")
        title = f"📅 <b>تقویم این هفته ({start} تا {end}):</b>"
    else:
        today = now.strftime("%Y-%m-%d")
        events = await secretary.get_events(message.chat.id, start_from=f"{today}T00:00:00", end_before=f"{today}T23:59:59")
        title = f"📅 <b>تقویم امروز ({today}):</b>"

    if not events:
        await message.answer(f"{title}\n\n📭 هیچ رویدادی نیست.", parse_mode="HTML")
        return

    lines = [title + "\n"]
    for e in events:
        loc = f" 📍 {e.location}" if e.location else ""
        lines.append(f"🕐 {e.start_time[11:16]} - {e.title}{loc}")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("event"))
async def cmd_event(message: Message, secretary: SecretaryManager):
    """Add calendar event: /event [time] [title]"""
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            "📅 <b>افزودن رویداد:</b> <code>/event [زمان] [عنوان]</code>\n\n"
            "<b>مثال:</b>\n"
            "• <code>/event 14:30 جلسه تیم</code>\n"
            "• <code>/event فردا ۱۰:۰۰ ملاقات با دکتر</code>",
            parse_mode="HTML",
        )
        return

    time_str = args[1]
    title = args[2]

    dt = parse_persian_datetime(time_str)
    if not dt:
        try:
            dt = datetime.fromisoformat(time_str)
        except ValueError:
            await message.answer("❌ فرمت زمان نامعتبر.")
            return

    end_dt = dt + timedelta(hours=1)
    event = await secretary.add_event(
        chat_id=message.chat.id,
        title=title,
        start_time=dt.isoformat(),
        end_time=end_dt.isoformat(),
    )

    await message.answer(
        f"📅 <b>رویداد ثبت شد</b>\n\n"
        f"🕐 <b>شروع:</b> {dt.strftime('%Y-%m-%d %H:%M')}\n"
        f"🕑 <b>پایان:</b> {end_dt.strftime('%H:%M')}\n"
        f"📝 <b>عنوان:</b> {title}\n\n"
        f"آی‌دی: <code>{event.id}</code>",
        parse_mode="HTML",
    )


@router.message(Command("summary"))
async def cmd_summary(message: Message, secretary: SecretaryManager):
    """Daily/weekly summary: /summary [today|week]"""
    args = message.text.split(maxsplit=1)
    period = args[1].lower() if len(args) > 1 else "today"

    if period in ("week", "هفته", "weekly"):
        summary = await secretary.get_weekly_summary(message.chat.id)
    else:
        summary = await secretary.get_daily_summary(message.chat.id)

    await message.answer(summary, parse_mode="HTML")


@router.message(Command("secretary"))
async def cmd_secretary(message: Message):
    """Secretary mode help."""
    text = (
        "🤖 <b>حالت سکرتر جاوید</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "من هم می‌تونم چت کنم و هم سکرتر شخصی‌ات باشم!\n\n"
        "📋 <b>دستورات سکرتر:</b>\n"
        "┌────────────────────────────────┐\n"
        "│ <code>/remind</code> [زمان] [متن]    │ یادآوری│\n"
        "│ <code>/task add</code> [متن]         │ تسک جدید  │\n"
        "│ <code>/tasks</code>                 │ لیست تسک‌ها│\n"
        "│ <code>/note</code> [متن]            │ یادداشت   │\n"
        "│ <code>/notes</code>                 │ همه یادداشت‌ها│\n"
        "│ <code>/event</code> [زمان] [عنوان]   │ رویداد تقویم│\n"
        "│ <code>/calendar</code> [today|week] │ نمایش تقویم│\n"
        "│ <code>/summary</code> [today|week]  │ گزارش روزانه/هفتگی│\n"
        "└────────────────────────────────┘\n\n"
        "💬 <b>یا به زبان طبیعی بگو:</b>\n"
        "• \"یادآوری کن فردا ساعت ۹ جلسه دارم\"\n"
        "• \"تسک جدید: خرید شیر\"\n"
        "• \"یادداشت: تلفن علی ۰۹۱۲...\"\n"
        "• \"تقویم: جلسه با تیم هفته بعد ساعت ۱۰\"\n"
        "• \"خلاصه امروز رو بده\"\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "دیتا فقط برای تو (مالک) ذخیره میشه 🔒"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())


# ========== NATURAL LANGUAGE HANDLER ==========

@router.message(
    ChatTypeFilter([ChatType.PRIVATE]),
    F.text,
)
async def handle_secretary_natural(message: Message, secretary: SecretaryManager, owner_id: int):
    """Intercept messages for secretary natural language processing."""
    if message.from_user.id != owner_id:
        return

    text = message.text.strip()
    if text.startswith("/"):
        return

    chat_id = message.chat.id
    processed = await _process_secretary_message(message, secretary, text, chat_id)
    if processed:
        return