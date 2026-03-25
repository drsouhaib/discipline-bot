from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.scheduler.jobs import morning_lock_callback_handler, plan_decision_callback_handler

async def morning_lock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle morning lock button press."""
    user_id = update.callback_query.from_user.id
    handled = await morning_lock_callback_handler(update, context, user_id)
    if not handled:
        # Fallback: maybe it's the old style (for onboarding)
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Morning confirmation received. Continuing...")

async def plan_decision_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plan decision (same/change)."""
    user_id = update.callback_query.from_user.id
    handled = await plan_decision_callback_handler(update, context, user_id)
    if not handled:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Plan decision received.")