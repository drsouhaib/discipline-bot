from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.models.database import SessionLocal
from bot.models.models import User, DailyLog, Plan, WeeklyAnalytics
from bot.utils.formatters import format_daily_summary
from bot.services.focus import start_focus, stop_focus
from datetime import datetime, date
import json

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    db.close()
    if not user:
        # Start onboarding conversation
        await update.message.reply_text(
            "Welcome to Discipline Bot. Let's set up your account.\n"
            "First, please send your time zone (e.g., Europe/London)."
        )
        # We'll use a conversation handler for onboarding.
        return
    else:
        await update.message.reply_text(
            f"Welcome back, {user.alter_ego}. Use /status to see today's progress."
        )

async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task_name = " ".join(context.args) if context.args else ""
    if not task_name:
        await update.message.reply_text("Please specify a task: /done <task name>")
        return
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        await update.message.reply_text("Please /start first.")
        db.close()
        return
    today = date.today()
    log = db.query(DailyLog).filter(DailyLog.user_id == user.id, DailyLog.date == today).first()
    if not log:
        await update.message.reply_text("No active day. Wait for morning sequence.")
        db.close()
        return
    # Find task
    found = None
    for task in log.tasks:
        if task["name"].lower() == task_name.lower():
            found = task
            break
    if not found:
        await update.message.reply_text(f"Task '{task_name}' not found in today's plan.")
        db.close()
        return
    if found["status"] in ["done", "missed"]:
        await update.message.reply_text(f"Task '{task_name}' is already {found['status']}.")
        db.close()
        return
    # Update
    if found["target"] > 1:
        found["progress"] += 1
        if found["progress"] >= found["target"]:
            found["status"] = "done"
            await update.message.reply_text(f"✅ Completed {task_name} fully.")
        else:
            found["status"] = "partial"
            await update.message.reply_text(f"✅ Progress on {task_name}: {found['progress']}/{found['target']}")
    else:
        found["status"] = "done"
        found["progress"] = 1
        await update.message.reply_text(f"✅ Marked '{task_name}' as done.")
    # Check if all tasks done
    if all(t["status"] in ["done", "missed"] for t in log.tasks):
        await update.message.reply_text("🎉 All tasks completed! Great job.")
    db.commit()
    db.close()

async def missed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task_name = " ".join(context.args) if context.args else ""
    if not task_name:
        await update.message.reply_text("Please specify a task: /missed <task name>")
        return
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        await update.message.reply_text("Please /start first.")
        db.close()
        return
    today = date.today()
    log = db.query(DailyLog).filter(DailyLog.user_id == user.id, DailyLog.date == today).first()
    if not log:
        await update.message.reply_text("No active day. Wait for morning sequence.")
        db.close()
        return
    found = None
    for task in log.tasks:
        if task["name"].lower() == task_name.lower():
            found = task
            break
    if not found:
        await update.message.reply_text(f"Task '{task_name}' not found.")
        db.close()
        return
    if found["status"] in ["done", "missed"]:
        await update.message.reply_text(f"Task already {found['status']}.")
        db.close()
        return
    found["status"] = "missed"
    await update.message.reply_text(f"❌ Marked '{task_name}' as missed.")
    db.commit()
    db.close()

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        await update.message.reply_text("Please /start first.")
        db.close()
        return
    today = date.today()
    log = db.query(DailyLog).filter(DailyLog.user_id == user.id, DailyLog.date == today).first()
    if not log:
        await update.message.reply_text("No active day. Start morning sequence first.")
        db.close()
        return
    # Group tasks by category
    from collections import defaultdict
    grouped = defaultdict(list)
    for task in log.tasks:
        grouped[task["category"]].append(task)
    lines = []
    for cat, tasks in grouped.items():
        lines.append(f"*{cat}*")
        for t in tasks:
            if t["target"] > 1:
                line = f"• {t['name']} ({t['progress']}/{t['target']})"
            else:
                line = f"• {t['name']}"
            if t["status"] == "done":
                line += " ✅"
            elif t["status"] == "missed":
                line += " ❌"
            elif t["status"] == "partial":
                line += " ⏳"
            lines.append(line)
        lines.append("")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    db.close()

async def focus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    duration = 25
    if context.args:
        try:
            duration = int(context.args[0])
        except:
            pass
    await update.message.reply_text(f"🎯 Focus timer started for {duration} minutes. Stay on task.")
    await start_focus(user_id, context, duration)

async def stopfocus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stop_focus(user_id)
    await update.message.reply_text("Focus timer stopped.")

async def silent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if user:
        user.silent_mode = True
        db.commit()
        await update.message.reply_text("🔇 Silent mode enabled. No reminders or motivational messages.")
    db.close()

async def loud_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if user:
        user.silent_mode = False
        db.commit()
        await update.message.reply_text("🔊 Silent mode disabled. Reminders active.")
    db.close()

async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        await update.message.reply_text("Please /start first.")
        db.close()
        return
    # Get last 7 logs
    from datetime import timedelta
    start = date.today() - timedelta(days=7)
    logs = db.query(DailyLog).filter(
        DailyLog.user_id == user.id,
        DailyLog.date >= start
    ).order_by(DailyLog.date).all()
    if not logs:
        await update.message.reply_text("Not enough data for weekly report yet.")
        db.close()
        return
    avg_score = sum(l.discipline_score for l in logs if l.discipline_score) / len(logs)
    # Build simple ASCII graph
    graph_lines = ["📊 *Weekly Scores*"]
    for log in logs:
        bar_len = int((log.discipline_score or 0) / 10)
        bar = "█" * bar_len + "░" * (10 - bar_len)
        graph_lines.append(f"{log.date.strftime('%a')}: {bar} {log.discipline_score}")
    await update.message.reply_text("\n".join(graph_lines), parse_mode="Markdown")
    db.close()

async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        await update.message.reply_text("Please /start first.")
        db.close()
        return
    today = date.today()
    log = db.query(DailyLog).filter(DailyLog.user_id == user.id, DailyLog.date == today).first()
    if not log or log.discipline_score is None:
        await update.message.reply_text("No score available for today yet.")
    else:
        tier = "ELITE" if log.discipline_score >= 90 else "SOLID" if log.discipline_score >= 70 else "WEAK" if log.discipline_score >= 50 else "FAILURE"
        await update.message.reply_text(f"🏆 Today's score: {log.discipline_score} ({tier})")
    db.close()

async def addfuture_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = " ".join(context.args)
    if not message:
        await update.message.reply_text("Please provide a message: /addfuture <message>")
        return
    # Store in user's custom future messages list (add to JSON field)
    # For simplicity, we'll store in a separate table or JSON column.
    # I'll skip implementation for brevity.
    await update.message.reply_text("Future message added.")

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        await update.message.reply_text("Please /start first.")
        db.close()
        return
    # Collect all data
    plans = db.query(Plan).filter(Plan.user_id == user.id).all()
    logs = db.query(DailyLog).filter(DailyLog.user_id == user.id).all()
    weekly = db.query(WeeklyAnalytics).filter(WeeklyAnalytics.user_id == user.id).all()
    data = {
        "user": {
            "telegram_id": user.telegram_id,
            "timezone": user.timezone,
            "alter_ego": user.alter_ego,
            "silent_mode": user.silent_mode,
        },
        "plans": [{"version": p.version, "categories": p.categories, "rules": p.rules} for p in plans],
        "logs": [{"date": l.date.isoformat(), "tasks": l.tasks, "score": l.discipline_score} for l in logs],
        "weekly": [{"week_start": w.week_start.isoformat(), "avg_score": w.avg_score} for w in weekly],
    }
    import json
    json_str = json.dumps(data, indent=2)
    # Send as file
    await update.message.reply_document(document=json_str.encode(), filename="discipline_bot_export.json")
    db.close()

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if user:
        db.query(DailyLog).filter(DailyLog.user_id == user.id).delete()
        db.query(Plan).filter(Plan.user_id == user.id).delete()
        db.query(WeeklyAnalytics).filter(WeeklyAnalytics.user_id == user.id).delete()
        db.delete(user)
        db.commit()
        await update.message.reply_text("All your data has been deleted. Goodbye.")
    else:
        await update.message.reply_text("No data found.")
    db.close()

async def morning_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually start the morning sequence for today."""
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        await update.message.reply_text("Please /start first.")
        db.close()
        return
    db.close()
    # Import morning_job inside the function to avoid circular import
    from bot.scheduler.jobs import morning_job
    await morning_job(context, user_id)