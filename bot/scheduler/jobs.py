import logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.models.database import SessionLocal
from bot.models.models import User, Plan, DailyLog
from bot.services.planner import create_daily_tasks_from_plan
from bot.utils.time_utils import parse_time_string
import pytz

logger = logging.getLogger(__name__)

# In-memory state for ongoing morning conversations (user_id -> dict)
morning_states = {}

# ---------- Morning Job Functions ----------
async def morning_job(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Start the morning sequence for a user."""
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        logger.error(f"User {user_id} not found for morning job.")
        db.close()
        return
    db.close()

    await context.bot.send_message(
        chat_id=user_id,
        text="Good morning! What time did you wake up? (e.g., 06:30)"
    )
    morning_states[user_id] = {"step": 0}

def schedule_morning_job(scheduler, user_id: int, wake_up_time: str, timezone_str: str):
    """Schedule the morning job at the user's wake_up_time daily."""
    from apscheduler.triggers.cron import CronTrigger
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
    logger.info(f"Scheduled morning job for user {user_id} at {wake_up_time} {timezone_str}")

async def handle_morning_message(update, context):
    """Called from a message handler when a user is in a morning sequence."""
    user_id = update.effective_user.id
    state = morning_states.get(user_id)
    if not state:
        return  # not in morning mode

    step = state.get("step")
    if step == 0:
        # Expecting wake-up time
        wake_up = update.message.text.strip()
        if not parse_time_string(wake_up):
            await update.message.reply_text("Invalid time. Use HH:MM (e.g., 06:30).")
            return
        state["wake_up"] = wake_up
        keyboard = [[InlineKeyboardButton("✅ I'm up", callback_data="morning_lock")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Confirm you are awake and starting your day.",
            reply_markup=reply_markup
        )
        state["step"] = 1

async def morning_lock_callback_handler(update, context, user_id):
    """Handle the morning lock button press."""
    state = morning_states.get(user_id)
    if not state or state.get("step") != 1:
        return False

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Same plan", callback_data="plan_same")],
        [InlineKeyboardButton("Change plan", callback_data="plan_change")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"Wake‑up time {state['wake_up']} recorded.\nSame plan as yesterday?",
        reply_markup=reply_markup
    )
    state["step"] = 2
    return True

async def plan_decision_callback_handler(update, context, user_id):
    """Handle plan decision (same or change)."""
    state = morning_states.get(user_id)
    if not state or state.get("step") != 2:
        return False

    query = update.callback_query
    await query.answer()
    choice = query.data

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        await query.edit_message_text("User not found. Please /start first.")
        db.close()
        del morning_states[user_id]
        return True

    if choice == "plan_same":
        plan = db.query(Plan).filter(Plan.user_id == user.id).order_by(Plan.version.desc()).first()
        if not plan:
            await query.edit_message_text("No plan found. Please /start to set up a plan.")
            db.close()
            del morning_states[user_id]
            return True
        categories = plan.categories
        tasks = create_daily_tasks_from_plan(categories)
        log = DailyLog(
            user_id=user.id,
            date=datetime.utcnow().date(),
            tasks=tasks,
            wake_up_time=state["wake_up"],
            morning_confirmed=True,
            morning_late=False,
            weak_start=False
        )
        db.add(log)
        db.commit()
        db.close()
        await query.edit_message_text(
            f"Day started! You have {len(tasks)} tasks. I'll remind you every {user.reminder_interval_hours} hours."
        )
    else:  # plan_change
        await query.edit_message_text(
            "Please send your new plan in the required format.\n"
            "I'll start the day after I receive it."
        )
        state["step"] = 3
        state["awaiting_plan"] = True
        db.close()
        return True

    del morning_states[user_id]
    return True

async def handle_new_plan_during_morning(update, context):
    """When user sends a plan while in morning sequence and expecting it."""
    user_id = update.effective_user.id
    state = morning_states.get(user_id)
    if not state or state.get("step") != 3:
        return

    plan_text = update.message.text
    from bot.services.planner import parse_plan_text
    categories, rules = parse_plan_text(plan_text)
    if not categories:
        await update.message.reply_text("Could not parse plan. Please try again.")
        return

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        await update.message.reply_text("User not found. Please /start first.")
        db.close()
        del morning_states[user_id]
        return

    db.query(Plan).filter(Plan.user_id == user.id).delete()
    new_plan = Plan(
        user_id=user.id,
        categories=categories,
        rules=rules
    )
    db.add(new_plan)
    db.commit()

    tasks = create_daily_tasks_from_plan(categories)
    log = DailyLog(
        user_id=user.id,
        date=datetime.utcnow().date(),
        tasks=tasks,
        wake_up_time=state["wake_up"],
        morning_confirmed=True,
        morning_late=False,
        weak_start=False
    )
    db.add(log)
    db.commit()
    db.close()

    await update.message.reply_text(
        f"New plan saved. Day started! You have {len(tasks)} tasks."
    )
    del morning_states[user_id]