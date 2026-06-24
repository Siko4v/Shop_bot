
import os
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web  # Веб-сервер үшін қажетті кітапхана

# Бот токенін осында жазыңыз
BOT_TOKEN = "8814191749:AAH2wj24nJGvNPPDyWu5C0i-4FcNXo0MV0o"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- ДЕРЕКТЕР ҚОРЫН БАСТАУ ---
conn = sqlite3.connect("shop_expenses.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        category TEXT,
        item TEXT,
        amount REAL,
        payment_method TEXT
    )
''')
conn.commit()

# --- FSM (Күйлерді басқару) ---
class ExpenseForm(StatesGroup):
    waiting_for_custom_category = State()
    waiting_for_custom_item = State()
    waiting_for_amount = State()
    waiting_for_custom_payment = State()
    waiting_for_period_start = State()
    waiting_for_period_end = State()

# --- RENDER ҮШІН ВЕБ-СЕРВЕР (24/7 ЖҰМЫС ІСТЕТУ СЕРВЕРІ) ---
async def handle(request):
    return web.Response(text="Expense Bot is running 24/7 successfully!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render автоматты түрде беретін портты оқиды, әйтпесе 8080 қолданады
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Web server started on port {port}")

# --- КӨМЕКШІ ФУНКЦИЯ: ХАБАРЛАМАНЫ 10 СЕКУНДТАН КЕЙІН ӨШІРУ ---
async def delete_after_delay(chat_id: int, message_id: int, delay: int = 10):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass 

# --- ПЕРНЕТАҚТАЛАР (KEYBOARDS) ---
def main_menu():
    kb = [
        [InlineKeyboardButton(text="💸 Шығын енгізу", callback_data="add_expense")],
        [InlineKeyboardButton(text="📅 Бүгінгі шығындар", callback_data="today_expenses")],
        [InlineKeyboardButton(text="📅 1 айлық шығын", callback_data="month_expenses")],
        [InlineKeyboardButton(text="⏳ Белгіленген мерзім шығыны", callback_data="period_expenses")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def categories_menu():
    kb = [
        [InlineKeyboardButton(text="Базар", callback_data="cat_Базар"), InlineKeyboardButton(text="Фирма", callback_data="cat_Фирма")],
        [InlineKeyboardButton(text="Шымкент", callback_data="cat_Шымкент"), InlineKeyboardButton(text="Басқа ✍️", callback_data="cat_custom")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def bazar_items_menu():
    kb = [
        [InlineKeyboardButton(text="Темекі", callback_data="item_Темекі"), InlineKeyboardButton(text="Құрт", callback_data="item_Құрт")],
        [InlineKeyboardButton(text="Басқа ✍️", callback_data="item_custom")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def payment_menu():
    kb = [
        [InlineKeyboardButton(text="Каспи", callback_data="pay_Каспи"), InlineKeyboardButton(text="Касса", callback_data="pay_Касса")],
        [InlineKeyboardButton(text="Д мырза", callback_data="pay_Д мырза"), InlineKeyboardButton(text="Басқа ✍️", callback_data="pay_custom")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def report_type_menu(prefix):
    kb = [
        [InlineKeyboardButton(text="📊 Жалпы шығындар", callback_data=f"{prefix}_total")],
        [InlineKeyboardButton(text="🔍 Жеке-жеке шығындар", callback_data=f"{prefix}_detail")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- БОТ СТАРТЫ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    today_str = datetime.now().strftime("%Y-%m-%d")
    await message.answer(f"📅 Бүгінгі күн: **{today_str}**\nТөмендегі мәзірді пайдаланыңыз:", reply_markup=main_menu(), parse_mode="Markdown")

# --- ШЫҒЫН ЕНГІЗУ ПРОЦЕСІ ---
@dp.callback_query(F.data == "add_expense")
async def process_add_expense(callback: types.CallbackQuery):
    msg = await callback.message.answer("Санатты таңдаңыз:", reply_markup=categories_menu())
    asyncio.create_task(delete_after_delay(callback.message.chat.id, msg.message_id))
    await callback.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    if category == "custom":
        msg = await callback.message.answer("Санат атауын енгізіңіз:")
        await state.set_state(ExpenseForm.waiting_for_custom_category)
        asyncio.create_task(delete_after_delay(callback.message.chat.id, msg.message_id))
    elif category == "Базар":
        await state.update_data(category=category)
        msg = await callback.message.answer("Тауар түрін таңдаңыз:", reply_markup=bazar_items_menu())
        asyncio.create_task(delete_after_delay(callback.message.chat.id, msg.message_id))
    else:  
        await state.update_data(category=category, item=category) 
        msg = await callback.message.answer(f"'{category}' үшін сомманы енгізіңіз:")
        await state.set_state(ExpenseForm.waiting_for_amount)
        asyncio.create_task(delete_after_delay(callback.message.chat.id, msg.message_id))
    await callback.answer()

@dp.message(ExpenseForm.waiting_for_custom_category)
async def custom_category_input
