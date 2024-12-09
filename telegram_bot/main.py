from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
sys.path.append(os.path.join(sys.path[0], '../'))
from src.routes.global_counter.counter import get_current_counter, nullify_counter
from src.database import async_session_maker
from src.routes.ticket.ticket import update_ticket_telegram_id
from src.config import TELEGRAM_TOKEN


bot = Bot(TELEGRAM_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    args = message.get_args()
    telegram_id = message.chat.id
    async with async_session_maker() as session:
        if args:
            added = await update_ticket_telegram_id(session, args, telegram_id)
            if added:
                if added.language == 'English':
                    await message.reply(f"👋🏻 {added.full_name}, your number is {added.number}. \n⚠️ You will receive a notification when it's your turn ⚡️")
                elif added.language == 'Қазақ':
                    await message.reply(f"👋🏻 {added.full_name} сіздің нөміріңіз {added.number}. \n⚠️ Кезегіңіз келгенде хабарлама келеді ⚡️")
                elif added.language == 'Русский':
                    await message.reply(f"👋🏻 {added.full_name}, ваш номер {added.number}. \n⚠️ Вы получите уведомление, когда ваша очередь подойдет ⚡️")

            await bot.send_message(-1002245461718, f"TIKCET\nFULL NAME: {added.full_name}\nTELEGRAM ID: {telegram_id}\nNUMBER: {added.number}\nLANGUAGE: {added.language}\nPHONE NUMBER: {added.phone_number}\nTOKEN: {args}")
        else:
            await message.reply("Привет 👋🏻")
            
@dp.message_handler(commands=['nullify_counter'])
async def nullify_counterк(message: types.Message):
    async with async_session_maker() as session:
        count = await nullify_counter(session)
        if count:
            await message.reply("Счетчик сброшен✅")
        else:
            await message.reply("Ошибка при сбросе счетчика❗️")
            
@dp.message_handler(commands=['get_current_counter'])
async def get_current_counter_by_telegem(message: types.Message):
    async with async_session_maker() as session:
        counter = await get_current_counter(session)
        await message.reply(f"Текущий счетчик: {counter}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    