import logging
import sys
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from bot.config import BOT_TOKEN, LOG_LEVEL
from bot.handlers.commands import *
from bot.handlers.conversations import *
from bot.handlers.callbacks import morning_lock_callback
from bot.scheduler.jobs import schedule_morning_job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from bot.models.database import engine, create_tables, Base
import pytz

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup APScheduler with persistent store
try:
    jobstores = {
        'default': SQLAlchemyJobStore(url=engine.url)
    }
    scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=pytz.UTC)
except Exception as e:
    logger.error(f"Failed to create scheduler: {e}")
    sys.exit(1)

# Create database tables BEFORE starting scheduler or bot
try:
    logger.info("Creating database tables...")
    create_tables()
    logger.info("Tables created (if they didn't exist).")
    logger.info(f"Using database: {engine.url}")
except Exception as e:
    logger.error(f"Failed to create tables: {e}")
    sys.exit(1)

# Start the scheduler
scheduler.start()

# Define the bot command menu (visible when user types "/")
commands = [
    BotCommand("start", "Start the bot (onboarding)"),
    BotCommand("morning", "Manually start the morning sequence"),
    BotCommand("status", "View today's progress"),
    BotCommand("done", "Mark a task done (e.g., /done Fajr)"),
    BotCommand("missed", "Mark a task missed"),
    BotCommand("focus", "Start a focus timer (e.g., /focus 25)"),
    BotCommand("score", "Show today's discipline score"),
    BotCommand("weekly", "Weekly report"),
    BotCommand("silent", "Disable reminders for today"),
    BotCommand("loud", "Enable reminders"),
    BotCommand("export", "Export all your data"),
    BotCommand("delete", "Delete all your data"),
]

async def post_init(application: Application):
    """Set the command menu when the bot starts."""
    await application.bot.set_my_commands(commands)
    logger.info("Command menu set.")

def main():
    # Create the application with post_init callback
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Conversation handler for onboarding
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_onboarding)],
        states={
            TIMEZONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, timezone_input)],
            PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, plan_input)],
            ALTER_EGO: [MessageHandler(filters.TEXT & ~filters.COMMAND, alter_ego_input)],
            REMINDER_INTERVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, reminder_interval_input)],
            MORNING_LOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, morning_lock_input)],
            WAKE_UP_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, wake_up_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_onboarding)],
    )

    # Register all handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("done", done_command))
    application.add_handler(CommandHandler("missed", missed_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("focus", focus_command))
    application.add_handler(CommandHandler("stopfocus", stopfocus_command))
    application.add_handler(CommandHandler("silent", silent_command))
    application.add_handler(CommandHandler("loud", loud_command))
    application.add_handler(CommandHandler("weekly", weekly_command))
    application.add_handler(CommandHandler("score", score_command))
    application.add_handler(CommandHandler("addfuture", addfuture_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CommandHandler("delete", delete_command))
    application.add_handler(CommandHandler("morning", morning_command))
    application.add_handler(CallbackQueryHandler(morning_lock_callback, pattern="morning_lock"))

    # Start the bot
    logger.info("Starting bot...")
    application.run_polling()

if __name__ == "__main__":
    main()