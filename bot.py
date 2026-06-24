
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# Логтарды қосу (Render-де боттың жұмысын көріп отыру үшін)
logging.basicConfig(level=logging.INFO)

# БОТ ТОКЕНІН ОСЫ ЖЕРГЕ ЖАЗЫҢЫЗ:
TOKEN = "8814191749:AAH2wj24nJGvNPPDyWu5C0i-4FcNXo0MV0o"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ------------------------------------------------------------
# RENDER ҮШІН ТЕГІН ВЕБ-СЕРВЕР (Порт қатесін айналып өту)
# ------------------------------------------------------------
async def handle(request):
    return web.Response(text="Bot is running successfully!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render автоматты түрде PORT айнымалысын береді, егер жоқ болса 8080 қолданады
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Web server started on port {port}")
# ------------------------------------------------------------

# СІЗДІҢ ЕСКІ КОДТАРЫҢЫЗ (HANDLER-ЛЕР) ОЙЫНДА ТҰРАДЫ:
# Мысалы, қарапайым /start командасы:
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Сәлем! Бот Render-де тегін және сәтті жұмыс істеп тұр! 🚀")

# Өзіңіздің қалған батырмаларыңыз бен функцияларыңызды (Handlers) 
# дәл осы жерден төмен қарай қоса берсеңіз болады...


# НЕГІЗГІ ІСКЕ ҚОСУ ФУНКЦИЯСЫ
async def main():
    # Алдымен Render-ді алдайтын веб-серверді іске қосамыз
    await start_web_server()
    
    # Кейін Телеграм боттың өзін іске қосамыз
    logging.info("Starting bot polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
