from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from bot.models.database import SessionLocal
from bot.models.models import User, Plan, DailyLog
from bot.services.planner import parse_plan_text, create_daily_tasks_from_plan
from bot.utils.time_utils import parse_time_string
import pytz

# Conversation states for onboarding
TIMEZONE, PLAN, ALTER_EGO, REMINDER_INTERVAL, MORNING_LOCK, WAKE_UP_TIME = range(6)

async def start_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Welcome to Discipline Bot! Let's set up your account.\n\n"
        "Please enter your time zone (e.g., Europe/London, America/New_York)."
    )
    return TIMEZONE

async def timezone_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz_str = update.message.text.strip()
    if tz_str not in pytz.all_timezones:
        mapping = {"algeria": "Africa/Algiers", "usa": "America/New_York", "uk": "Europe/London"}
        if tz_str.lower() in mapping:
            tz_str = mapping[tz_str.lower()]
        else:
            await update.message.reply_text("Invalid time zone. Please try again.")
            return TIMEZONE
    context.user_data["timezone"] = tz_str
    await update.message.reply_text("Great. Now send your daily plan in the required format.\n"
                                    "Use the format with sections and bullet points.")
    return PLAN

async def plan_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan_text = update.message.text
    categories, rules = parse_plan_text(plan_text)
    if not categories:
        await update.message.reply_text("Could not parse plan. Please check format and send again.")
        return PLAN
    context.user_data["categories"] = categories
    context.user_data["rules"] = rules
    await update.message.reply_text("Plan accepted. Now enter your alter ego name (e.g., Iron Version).")
    return ALTER_EGO

async def alter_ego_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    alter_ego = update.message.text.strip()
    context.user_data["alter_ego"] = alter_ego
    await update.message.reply_text(f"Your alter ego: {alter_ego}\n"
                                    "How many hours between reminders? (default 2)")
    return REMINDER_INTERVAL

async def reminder_interval_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        interval = int(update.message.text)
    except:
        interval = 2
    context.user_data["reminder_interval"] = interval
    await update.message.reply_text("Morning lock timeout in minutes? (default 30)")
    return MORNING_LOCK

async def morning_lock_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        lock_minutes = int(update.message.text)
    except:
        lock_minutes = 30
    context.user_data["morning_lock"] = lock_minutes
    await update.message.reply_text("What time do you usually wake up? (HH:MM, default 07:00)")
    return WAKE_UP_TIME

async def wake_up_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wake_up = update.message.text.strip()
        if not parse_time_string(wake_up):
            wake_up = "07:00"
        context.user_data["wake_up_time"] = wake_up

        db = SessionLocal()
        telegram_id = update.effective_user.id
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.timezone = context.user_data["timezone"]
            user.reminder_interval_hours = context.user_data["reminder_interval"]
            user.morning_lock_minutes = context.user_data["morning_lock"]
            user.wake_up_time = wake_up
            user.alter_ego = context.user_data["alter_ego"]
            user.last_active = datetime.utcnow()
            db.query(Plan).filter(Plan.user_id == user.id).delete()
            new_plan = Plan(
                user_id=user.id,
                categories=context.user_data["categories"],
                rules=context.user_data["rules"]
            )
            db.add(new_plan)
            db.commit()
        else:
            user = User(
                telegram_id=telegram_id,
                timezone=context.user_data["timezone"],
                reminder_interval_hours=context.user_data["reminder_interval"],
                morning_lock_minutes=context.user_data["morning_lock"],
                wake_up_time=wake_up,
                alter_ego=context.user_data["alter_ego"]
            )
            db.add(user)
            db.commit()
            plan = Plan(
                user_id=user.id,
                categories=context.user_data["categories"],
                rules=context.user_data["rules"]
            )
            db.add(plan)
            db.commit()
        db.close()

        await update.message.reply_text("Setup complete! Your first morning sequence will start tomorrow.")
        from bot.scheduler.jobs import schedule_morning_job
        from bot.main import scheduler
        schedule_morning_job(scheduler, telegram_id, user.wake_up_time, user.timezone)

    except Exception as e:
        await update.message.reply_text(f"Error: {e}. Please try /start again.")
    finally:
        context.user_data.clear()
        return ConversationHandler.END

async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Onboarding cancelled.")
    context.user_data.clear()
    return ConversationHandler.END