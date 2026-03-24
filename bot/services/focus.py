import asyncio
from telegram.ext import ContextTypes

class FocusTimer:
    def __init__(self, chat_id: int, duration_minutes: int, context: ContextTypes.DEFAULT_TYPE):
        self.chat_id = chat_id
        self.duration = duration_minutes * 60
        self.context = context
        self.running = True

    async def start(self):
        for i in range(0, self.duration, 300):
            if not self.running:
                break
            await asyncio.sleep(300)
            if self.running:
                await self.context.bot.send_message(
                    chat_id=self.chat_id,
                    text="⏳ Focus: Don't touch your phone. Stay on task."
                )
        if self.running:
            await self.context.bot.send_message(
                chat_id=self.chat_id,
                text="✅ Focus session complete. Good work."
            )
        self.running = False

    def stop(self):
        self.running = False

# In-memory store for active timers
active_focus = {}

async def start_focus(chat_id: int, context: ContextTypes.DEFAULT_TYPE, duration: int = 25):
    timer = FocusTimer(chat_id, duration, context)
    active_focus[chat_id] = timer
    asyncio.create_task(timer.start())

def stop_focus(chat_id: int):
    if chat_id in active_focus:
        active_focus[chat_id].stop()
        del active_focus[chat_id]