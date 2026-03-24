import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///discipline_bot.db")
DEFAULT_REMINDER_INTERVAL = int(os.getenv("DEFAULT_REMINDER_INTERVAL", 2))
DEFAULT_MORNING_LOCK_MINUTES = int(os.getenv("DEFAULT_MORNING_LOCK_MINUTES", 30))
DEFAULT_WAKE_UP_TIME = os.getenv("DEFAULT_WAKE_UP_TIME", "07:00")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")