import asyncio
import logging
import threading
import schedule
import time
from datetime import datetime as dt
import pytz
import sys
import os

sys.path.append(os.path.join(sys.path[0], '../'))
from src.routes.global_counter.counter import nullify_counter  # Ensure this is asynchronous if needed
from src.database import get_async_session, async_session_maker

sys.path.append(os.path.join(sys.path[0], '../'))
from telegram_bot.main import bot

logging.basicConfig(level=logging.INFO)

def greeting():
    current_time = dt.now(pytz.timezone('Asia/Almaty')).strftime("%Y-%m-%d %H:%M:%S %Z")
    logging.info("Hello, World!")
    logging.info(f"Current Server Time: {current_time}")
    asyncio.run(check_time())  # Use asyncio.ensure_future instead of asyncio.run()

async def check_time():
    async with async_session_maker() as session:
        count = await nullify_counter(session)
        if count:
            await bot.send_message(-1002245461718,"Сетчик сброшен✅")


schedule.every().day.at("18:00").do(greeting)
# schedule.every(10).seconds.do(greeting)


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    logging.info("Starting application...")
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)  # Keep the main thread alive, allowing background tasks to run
    except KeyboardInterrupt:
        logging.info("Program terminated.")
