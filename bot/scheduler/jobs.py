import logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.models.database import SessionLocal
from bot.models.models import User, Plan, DailyLog
from bot.services.planner import create_daily_tasks_from_plan
from bot.utils.time_utils import parse_time_string

logger = logging.getLogger(__name__)

# In-memory state for ongoing morning conversations (user_id -> step)
# Step 0: waiting for wake-up time; step 1: waiting for plan decision; step 2: done
morning_states = {}

async def morning_job(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Start the morning sequence for a user."""
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        logger.error(f"User {user_id} not found for morning job.")
        db.close()
        return
    db.close()

    # Ask for wake-up time
    await context.bot.send_message(
        chat_id=user_id,
        text="Good morning! What time did you wake up? (e.g., 06:30)"
    )
    # Set the state so that the next message from this user is handled as the wake-up time
    morning_states[user_id] = {"step": 0}

async def handle_morning_message(update, context, user_id):
    """Called from a message handler when a user is in a morning sequence."""
    state = morning_states.get(user_id)
    if not state:
        return False  # not in morning mode

    step = state.get("step")
    if step == 0:
        # Expecting wake-up time
        wake_up = update.message.text.strip()
        if not parse_time_string(wake_up):
            await update.message.reply_text("Invalid time. Use HH:MM (e.g., 06:30).")
            return True
        # Store wake-up time
        state["wake_up"] = wake_up
        # Send morning lock button
        keyboard = [[InlineKeyboardButton("✅ I'm up", callback_data="morning_lock")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Confirm you are awake and starting your day.",
            reply_markup=reply_markup
        )
        state["step"] = 1
        return True
    return False

async def morning_lock_callback_handler(update, context, user_id):
    """Handle the morning lock button press."""
    state = morning_states.get(user_id)
    if not state or state.get("step") != 1:
        return False

    query = update.callback_query
    await query.answer()

    # Ask about plan
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
        # Get latest plan
        plan = db.query(Plan).filter(Plan.user_id == user.id).order_by(Plan.version.desc()).first()
        if not plan:
            await query.edit_message_text("No plan found. Please /start to set up a plan.")
            db.close()
            del morning_states[user_id]
            return True
        categories = plan.categories
        rules = plan.rules
        # Create daily log
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
        # Schedule reminder jobs (to be implemented)
        # ...
    else:  # plan_change
        await query.edit_message_text(
            "Please send your new plan in the required format.\n"
            "I'll start the day after I receive it."
        )
        # Set state to wait for plan input
        state["step"] = 3
        state["awaiting_plan"] = True
        db.close()
        return True

    # Remove from morning state
    del morning_states[user_id]
    return True

async def handle_new_plan_during_morning(update, context, user_id):
    """When user sends a plan while in morning sequence and expecting it."""
    state = morning_states.get(user_id)
    if not state or state.get("step") != 3:
        return False

    plan_text = update.message.text
    from bot.services.planner import parse_plan_text
    categories, rules = parse_plan_text(plan_text)
    if not categories:
        await update.message.reply_text("Could not parse plan. Please try again.")
        return True

    # Save new plan
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        await update.message.reply_text("User not found. Please /start first.")
        db.close()
        del morning_states[user_id]
        return True

    # Delete old plan
    db.query(Plan).filter(Plan.user_id == user.id).delete()
    # Add new plan
    new_plan = Plan(
        user_id=user.id,
        categories=categories,
        rules=rules
    )
    db.add(new_plan)
    db.commit()

    # Create daily log
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
    # Schedule reminders
    # ...
    del morning_states[user_id]
    return True