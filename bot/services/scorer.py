def calculate_daily_score(
    tasks: list,
    morning_confirmed: bool,
    morning_late: bool,
    rule_violations: list,
    total_rules: int
) -> int:
    """Calculate discipline score 0-100."""
    # Morning component (10 points)
    if morning_confirmed:
        if morning_late:
            morning_score = 5
        else:
            morning_score = 10
    else:
        morning_score = 0

    # Task completion component (60 points)
    total_tasks = len(tasks)
    if total_tasks == 0:
        completion_score = 60
    else:
        # Weight per task = 60 / total_tasks
        task_points = 0
        for t in tasks:
            if t["status"] == "done":
                task_points += 60 / total_tasks
            elif t["status"] == "partial":
                # partial: progress / target
                progress_ratio = t["progress"] / t["target"] if t["target"] > 0 else 0
                task_points += (60 / total_tasks) * progress_ratio
        completion_score = task_points

    # On-time completion (20 points)
    on_time_count = sum(1 for t in tasks if t.get("completed_before_bedtime", False))
    on_time_score = (on_time_count / total_tasks) * 20 if total_tasks else 20

    # Rule violations (10 points)
    rule_score = max(0, 10 - (len(rule_violations) * 2))

    total = morning_score + completion_score + on_time_score + rule_score
    return int(round(total))