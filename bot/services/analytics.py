from collections import Counter
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from bot.models.models import DailyLog, User
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

def detect_failure_patterns(db: Session, user: User) -> Tuple[List[Dict], str]:
    """Analyze last 7 days of logs, return most missed tasks and weak time period."""
    seven_days_ago = datetime.utcnow().date() - timedelta(days=7)
    logs = db.query(DailyLog).filter(
        DailyLog.user_id == user.id,
        DailyLog.date >= seven_days_ago
    ).all()
    if not logs:
        return [], ""

    # Count missed tasks
    missed_counter = Counter()
    for log in logs:
        for task in log.tasks:
            if task["status"] == "missed":
                missed_counter[task["name"]] += 1

    # Get tasks with miss rate >= 30%
    total_tasks_per_day = {log.date: len(log.tasks) for log in logs}
    # For simplicity, we just consider count of misses relative to number of days
    top_missed = []
    for name, count in missed_counter.most_common(3):
        if count / len(logs) >= 0.3:
            top_missed.append({"name": name, "miss_count": count})

    # Weak time period: not implemented fully – could use reminder timestamps if stored
    # Placeholder
    weak_period = "evening"  # dummy

    return top_missed, weak_period