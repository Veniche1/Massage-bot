from os import getenv
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from database import init_db
from handlers.commands import router as commands_router
from forms.registration import router as registration_router
from handlers.calendar import router as calendar_router
from handlers.admin import router as admin_router
from handlers.records import router as records_router
import aiosqlite
from datetime import datetime, timedelta
from handlers.reviews import router as reviews_router

load_dotenv()
TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()
dp.include_router(commands_router)   
dp.include_router(registration_router)
dp.include_router(calendar_router)
dp.include_router(admin_router)
dp.include_router(records_router)
dp.include_router(reviews_router)


async def send_reminders(bot: Bot):
    while True:
        now = datetime.now()
        if now.hour == 9 and now.minute == 0:
            async with aiosqlite.connect("users.db") as db:
                cursor = await db.execute(
                    "SELECT u.user_id, a.date, a.time FROM appointments a JOIN users u ON a.user_id = u.id WHERE a.date = ? AND a.status = 'confirmed'",
                    (now.strftime("%Y-%m-%d"),)
                )
                rows = await cursor.fetchall()
            
            for row in rows:
                try:
                    await bot.send_message(
                        row[0],
                        f"🔔 Напоминание!\nСегодня в {row[2]} у вас массаж.\nЖдем вас!"
                    )
                except:
                    pass

        async with aiosqlite.connect("users.db") as db:
            cursor = await db.execute(
                "SELECT u.user_id, a.date, a.time FROM appointments a JOIN users u ON a.user_id = u.id WHERE a.date = ? AND a.status = 'confirmed'",
                (now.strftime("%Y-%m-%d"),)
            )
            rows = await cursor.fetchall()

        for row in rows:
            try:
                app_hour, app_minute = map(int, row[2].split(":"))
                if app_hour == now.hour + 1 and app_minute == now.minute:
                    await bot.send_message(
                        row[0],
                        f"⏰Напоминание!\nЧерез 1 час у вас массаж в {row[2]}.\nНе опаздывайте!"
                    )
            except:
                pass

        await asyncio.sleep(60) 


async def main():
    await init_db()
    bot = Bot(token=TOKEN)
    asyncio.create_task(send_reminders(bot))
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())