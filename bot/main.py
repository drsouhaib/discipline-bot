import logging
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from bot.config import BOT_TOKEN, LOG_LEVEL
from bot.handlers.commands import *
from bot.handlers.conversations import *
from bot.handlers.callbacks import morning_lock_callback
from bot.scheduler.jobs import schedule_morning_job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from bot.models.database import engine, create_tables
import pytz

logging.basicConfig(level=getattr(logging, LOG_LEVEL))

# Setup APScheduler with persistent store
jobstores = {
    'default': SQLAlchemyJobStore(url=engine.url)
}
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=pytz.UTC)

# Create database tables
create_tables()

scheduler.start()

def main():
    application = Application.builder().token(BOT_TOKEN).build()

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
    application.add_handler(CallbackQueryHandler(morning_lock_callback, pattern="morning_lock"))

    application.run_polling()

if __name__ == "__main__":
    main()