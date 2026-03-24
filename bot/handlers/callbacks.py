from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def morning_lock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    # Mark morning confirmed in the user's daily log
    from bot.models.database import SessionLocal
    from bot.models.models import DailyLog, User
    from datetime import date
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if user:
        today = date.today()
        log = db.query(DailyLog).filter(DailyLog.user_id == user.id, DailyLog.date == today).first()
        if log:
            log.morning_confirmed = True
            # Check if late
            # We need to store the time of lock send vs press
            # For simplicity, assume not late
            db.commit()
    db.close()
    await query.edit_message_text("✅ Morning confirmed. Let's start the day.")
    # Continue with plan confirmation (could be a separate callback)