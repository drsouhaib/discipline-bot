def progress_bar(percent: float, length: int = 10) -> str:
    filled = int(length * percent / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"{bar} {percent:.0f}%"

def format_tasks_summary(tasks, category_name: str) -> str:
    lines = [f"*{category_name}*"]
    for task in tasks:
        name = task["name"]
        target = task["target"]
        progress = task["progress"]
        status = task["status"]
        if target > 1:
            line = f"• {name} ({progress}/{target})"
        else:
            line = f"• {name}"
        if status == "done":
            line += " ✅"
        elif status == "missed":
            line += " ❌"
        elif status == "partial":
            line += " ⏳"
        lines.append(line)
    return "\n".join(lines)

def format_daily_summary(log) -> str:
    tasks_done = sum(1 for t in log.tasks if t["status"] == "done")
    tasks_missed = sum(1 for t in log.tasks if t["status"] == "missed")
    total = len(log.tasks)
    percent = (tasks_done / total) * 100 if total else 0
    bar = progress_bar(percent)
    tier = "ELITE" if log.discipline_score >= 90 else "SOLID" if log.discipline_score >= 70 else "WEAK" if log.discipline_score >= 50 else "FAILURE"
    return f"""📅 *Day Summary*

✅ Done: {tasks_done}/{total}
❌ Missed: {tasks_missed}
📊 Progress: {bar}
🏆 Score: {log.discipline_score} ({tier})"""