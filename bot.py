
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiohttp import web

# Логтарды қосу
logging.basicConfig(level=logging.INFO)

# БОТ ТОКЕНІН ОСЫ ЖЕРГЕ ЖАЗЫҢЫЗ:
TOKEN = "8814191749:AAH2wj24nJGvNPPDyWu5C0i-4FcNXo0MV0o"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ------------------------------------------------------------
# RENDER ҮШІН ТЕГІН ВЕБ-СЕРВЕР (Порт қатесін айналып өту)
# ------------------------------------------------------------
async def handle(request):
    return web.Response(text="Shop Bot is running successfully!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Web server started on port {port}")
# ------------------------------------------------------------


# 1. БАС МӘЗІР БАТЫРМАЛАРЫ (REPLY KEYBOARD)
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🛍 Тауарлар каталогы")
    builder.button(text="ℹ️ Біз туралы")
    builder.button(text="📞 Байланыс")
    builder.adjust(1, 2) # Бірінші батырма бөлек, қалған екеуі қатар тұрады
    return builder.as_markup(resize_keyboard=True)


# 2. ТАУАРЛАР ТІЗІМІ (INLINE KEYBOARD)
def get_products_menu():
    builder = InlineKeyboardBuilder()
    # Тауарларды осы жерге қоса бересіз (Аты және тауар коды)
    builder.button(text="👟 Өнім 1 - Сәнді кроссовка", callback_data="prod_1")
    builder.button(text="👕 Өнім 2 - Худи (Black)", callback_data="prod_2")
    builder.button(text="🧢 Өнім 3 - Кепка", callback_data="prod_3")
    builder.adjust(1)
    return builder.as_markup()


# 3. /START КОМАНДАСЫ
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Сәлем, {message.from_user.full_name}! 👋\nДүкен ботымызға қош келдіңіз!\n\nТөмендегі мәзірді пайдаланып тауарларды көре аласыз:",
        reply_markup=get_main_menu()
    )


# 4. "ТАУАРЛАР КАТАЛОГЫ" БАТЫРМАСЫ БАСЫЛҒАНДА
@dp.message(lambda message: message.text == "🛍 Тауарлар каталогы")
async def show_catalog(message: types.Message):
    await message.answer("Біздің дүкендегі қолжетімді тауарлар:", reply_markup=get_products_menu())


# 5. "БІЗ ТУРАЛЫ" ЖӘНЕ "БАЙЛАНЫС" БАТЫРМАЛАРЫ
@dp.message(lambda message: message.text == "ℹ️ Біз туралы")
async def about_shop(message: types.Message):
    await message.answer("🏪 **Saryyy Shop** — ең сапалы әрі сәнді киімдер мен аяқ киімдер дүкені. Біз сізге ең үздік қызметті ұсынамыз!")

@dp.message(lambda message: message.text == "📞 Байланыс")
async def contact_us(message: types.Message):
    await message.answer("📞 Қолдау көрсету орталығы: @менеджер_аккаунты\n📍 Алматы қаласы\n🕒 Жұмыс уақыты: 10:00 - 22:00")


# 6. ТАУАРДЫҢ ӨЗІН БАСҚАНДА ШЫҒАТЫН АҚПАРАТ (CALLBACK)
@dp.callback_query(lambda call: call.data.startswith("prod_"))
async def product_click(call: types.CallbackQuery):
    product_id = call.data.split("_")[1]
    
    if product_id == "1":
        text = "👟 **Сәнді кроссовка**\n\n💰 Бағасы: 25 000 ₸\n📐 Өлшемдері: 40, 41, 42\nℹ️ Өте ыңғайлы әрі жеңіл аяқ киім."
    elif product_id == "2":
        text = "👕 **Худи (Black)**\n\n💰 Бағасы: 18 000 ₸\n📐 Өлшемдері: M, L, XL\nℹ️ 100% мақтадан жасалған жылы худи."
    elif product_id == "3":
        text = "🧢 **Кепка**\n\n💰 Бағасы: 7 000 ₸\nℹ️ Күннен қорғайтын сәнді бас киім."
        
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Сатып алу", callback_data=f"buy_{product_id}")
    builder.button(text="⬅️ Артқа", callback_data="back_to_catalog")
    
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await call.answer()


# 7. АРТҚА ҚАЙТУ БАТЫРМАСЫ
@dp.callback_query(lambda call: call.data == "back_to_catalog")
async def back_catalog(call: types.CallbackQuery):
    await call.message.edit_text("Біздің дүкендегі қолжетімді тауарлар:", reply_markup=get_products_menu())
    await call.answer()


# 8. САТЫП АЛУ БАТЫРМАСЫ БАСЫЛҒАНДА
@dp.callback_query(lambda call: call.data.startswith("buy_"))
async def buy_product(call: types.CallbackQuery):
    await call.message.answer("🎉 Тапсырысыңыз қабылданды! Менеджер сізбен жақын арада байланысады.")
    await call.answer()


# ИНТЕРНЕТ СЕРВЕР МЕН БОТТЫ ІСКЕ ҚОСУ
async def main():
    await start_web_server()
    logging.info("Starting bot polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
