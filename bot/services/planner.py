import re
from typing import List, Dict, Tuple, Optional

def parse_plan_text(plan_text: str) -> Tuple[List[Dict], List[str]]:
    """
    Parse user's plan text into:
    - categories: list of {name, tasks: [{name, target}]}
    - rules: list of strings
    """
    sections = re.split(r"\-{5,}", plan_text)
    categories = []
    rules = []

    for section in sections:
        lines = section.strip().split("\n")
        if not lines:
            continue
        # Extract section name from first line
        section_name = lines[0].strip().strip("— ").strip()
        if not section_name:
            continue
        if section_name == "Rules":
            # parse rules
            for line in lines[1:]:
                if line.startswith("•"):
                    rule_text = line[1:].strip()
                    rules.append(rule_text)
            continue

        tasks = []
        for line in lines[1:]:
            if line.startswith("•"):
                task_line = line[1:].strip()
                # Check for repeatable pattern: (X/Y) or (X) or (0 /Y)
                match = re.search(r"\((\d+)\s*/\s*(\d+)\)|\((\d+)\)", task_line)
                if match:
                    if match.group(1) is not None:
                        target = int(match.group(2))
                    else:
                        target = int(match.group(3))
                    # Remove the parentheses from the name
                    task_name = re.sub(r"\s*\(.*\)", "", task_line).strip()
                else:
                    target = 1
                    task_name = task_line
                tasks.append({"name": task_name, "target": target})
        if tasks:
            categories.append({"name": section_name, "tasks": tasks})
    return categories, rules

def create_daily_tasks_from_plan(plan_categories: List[Dict]) -> List[Dict]:
    """Create a fresh daily task list from a plan."""
    tasks = []
    for cat in plan_categories:
        for task in cat["tasks"]:
            tasks.append({
                "name": task["name"],
                "category": cat["name"],
                "target": task["target"],
                "progress": 0,
                "status": "pending",  # pending, partial, done, missed
                "completed_before_bedtime": False
            })
    return tasks