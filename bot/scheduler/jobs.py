import logging
from telegram.ext import ContextTypes
from bot.models.database import SessionLocal
from bot.models.models import User, DailyLog, Plan
from bot.services.planner import create_daily_tasks_from_plan
from bot.services.reminders import send_reminder
from bot.utils.time_utils import get_current_time_in_timezone, parse_time_string, format_time_for_user
from datetime import datetime, date
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import pytz

logger = logging.getLogger(__name__)

async def morning_job(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Run morning sequence for a specific user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            return

        # Ask wake-up time
        await context.bot.send_message(
            chat_id=user_id,
            text="🌅 Good morning! What time did you wake up? (e.g., 06:30)"
        )
        # We need to store that the morning sequence is pending for this user.
        # For simplicity, we'll set a flag in user model or handle in conversation.
        # Here we'll just send the message and rely on the user's response to continue.
        # However, the morning sequence has multiple steps; we need to manage state.
        # For brevity, I'll outline the flow but not implement full state machine.
        # In production, use ConversationHandler.

        # For demonstration, we'll proceed with a simplified version.
        # Actual implementation should use a conversation to handle multiple steps.
        # We'll implement the morning conversation in handlers/conversations.py.
        pass
    except Exception as e:
        logger.error(f"Error in morning_job for {user_id}: {e}")
    finally:
        db.close()

def schedule_morning_job(scheduler, user_id: int, wake_up_time: str, timezone_str: str):
    """Schedule the morning job at the user's wake_up_time daily."""
    tz = pytz.timezone(timezone_str)
    hour, minute = map(int, wake_up_time.split(":"))
    trigger = CronTrigger(hour=hour, minute=minute, timezone=tz)
    scheduler.add_job(
        morning_job,
        trigger=trigger,
        args=[user_id],
        id=f"morning_{user_id}",
        replace_existing=True
    )

def schedule_reminder_jobs(scheduler, user_id: int, interval_hours: int, start_time: datetime):
    """Schedule recurring reminders for a user starting at start_time."""
    # Remove existing reminder jobs for this user
    for job in scheduler.get_jobs():
        if job.id.startswith(f"reminder_{user_id}"):
            job.remove()
    # Schedule first reminder after interval
    trigger = IntervalTrigger(hours=interval_hours, start_date=start_time)
    scheduler.add_job(
        send_reminder,
        trigger=trigger,
        args=[user_id],
        id=f"reminder_{user_id}",
        replace_existing=True
    )