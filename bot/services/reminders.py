import logging
from telegram.ext import ContextTypes
from bot.models.database import SessionLocal
from bot.models.models import User, DailyLog
from bot.utils.time_utils import get_current_time_in_timezone, parse_time_string
from bot.utils.formatters import format_tasks_summary
from datetime import datetime, date

logger = logging.getLogger(__name__)

async def send_reminder(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Send reminder to user about pending tasks."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user or user.silent_mode:
            return
        # Find today's log
        today = datetime.utcnow().date()
        log = db.query(DailyLog).filter(
            DailyLog.user_id == user.id,
            DailyLog.date == today
        ).first()
        if not log:
            return
        # Collect pending and partial tasks
        pending = [t for t in log.tasks if t["status"] in ["pending", "partial"]]
        if pending:
            # Group by category
            grouped = {}
            for t in pending:
                cat = t["category"]
                grouped.setdefault(cat, []).append(t)
            lines = ["⏰ *Reminder:* Pending tasks:"]
            for cat, tasks in grouped.items():
                lines.append(f"\n*{cat}*")
                for t in tasks:
                    if t["target"] > 1:
                        lines.append(f"• {t['name']} ({t['progress']}/{t['target']})")
                    else:
                        lines.append(f"• {t['name']}")
            await context.bot.send_message(chat_id=user_id, text="\n".join(lines), parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=user_id, text="🔥 All tasks done! Keep going.")
    except Exception as e:
        logger.error(f"Error sending reminder to {user_id}: {e}")
    finally:
        db.close()