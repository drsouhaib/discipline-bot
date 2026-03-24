import math
from datetime import datetime, time
from typing import List, Dict, Optional
import numpy as np

def compute_sleep_duration(bedtime_str: str, wakeup_str: str) -> float:
    """Compute sleep duration in hours."""
    # Assume times are within the same night (bedtime after 18:00, wakeup before 12:00)
    # For simplicity, we treat as a simple diff with day wrap.
    bt = datetime.strptime(bedtime_str, "%H:%M")
    wu = datetime.strptime(wakeup_str, "%H:%M")
    if wu < bt:
        wu += timedelta(days=1)
    delta = wu - bt
    return delta.total_seconds() / 3600.0

def calculate_weekly_sleep_score(daily_logs: List[Dict]) -> Optional[int]:
    """Compute weekly sleep score (0-100) from list of daily logs."""
    durations = []
    bedtimes = []
    for log in daily_logs:
        if log.get("bedtime") and log.get("wake_up_time"):
            durations.append(compute_sleep_duration(log["bedtime"], log["wake_up_time"]))
            # Convert bedtime to minutes since midnight
            bt = datetime.strptime(log["bedtime"], "%H:%M")
            bedtimes.append(bt.hour * 60 + bt.minute)
    if not durations:
        return None

    # Duration score (optimal 7-8h)
    duration_scores = []
    for d in durations:
        if 7 <= d <= 8:
            duration_scores.append(100)
        elif d < 6:
            duration_scores.append(max(0, (d / 6) * 50))
        elif d > 9:
            duration_scores.append(max(0, 100 - ((d - 9) * 25)))
        else:
            # linear between 6-7 and 8-9
            if d < 7:
                score = 50 + ((d - 6) / 1) * 50
            else:  # >8
                score = 100 - ((d - 8) / 1) * 50
            duration_scores.append(score)

    avg_duration_score = sum(duration_scores) / len(duration_scores)

    # Consistency score: standard deviation of bedtimes (in minutes)
    if len(bedtimes) > 1:
        std = np.std(bedtimes)
        # Map std 0->100, std 120->0 linearly
        consistency_score = max(0, 100 - (std / 120) * 100)
    else:
        consistency_score = 50

    total_score = int(round(avg_duration_score * 0.5 + consistency_score * 0.5))
    return total_score