
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

# --- КӨМЕКШІ ФУНКЦИЯ: ХАБАРЛАМАНЫ 10 СЕКУНДТАН КЕЙІН ӨШІРУ ---
async def delete_after_delay(chat_id: int, message_id: int, delay: int = 10):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass # Хабарлама әлдеқашан өшірілген болса, қате шығармайды

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
    else:  # Фирма немесе Шымкент
        await state.update_data(category=category, item=category) # Өз аты тауар ретінде
        msg = await callback.message.answer(f"'{category}' үшін сомманы енгізіңіз:")
        await state.set_state(ExpenseForm.waiting_for_amount)
        asyncio.create_task(delete_after_delay(callback.message.chat.id, msg.message_id))
    await callback.answer()

@dp.message(ExpenseForm.waiting_for_custom_category)
async def custom_category_input(message: types.Message, state: FSMContext):
    asyncio.create_task(delete_after_delay(message.chat.id, message.message_id))
    await state.update_data(category=message.text, item=message.text)
    msg = await message.answer(f"'{message.text}' үшін сомманы енгізіңіз:")
    await state.set_state(ExpenseForm.waiting_for_amount)
    asyncio.create_task(delete_after_delay(message.chat.id, msg.message_id))

@dp.callback_query(F.data.startswith("item_"))
async def process_bazar_item(callback: types.CallbackQuery, state: FSMContext):
    item = callback.data.split("_")[1]
    if item == "custom":
        msg = await callback.message.answer("Тауар атауын жазыңыз:")
        await state.set_state(ExpenseForm.waiting_for_custom_item)
        asyncio.create_task(delete_after_delay(callback.message.chat.id, msg.message_id))
    else:
        await state.update_data(item=item)
        msg = await callback.message.answer(f"'{item}' үшін сомманы енгізіңіз:")
        await state.set_state(ExpenseForm.waiting_for_amount)
        asyncio.create_task(delete_after_delay(callback.message.chat.id, msg.message_id))
    await callback.answer()

@dp.message(ExpenseForm.waiting_for_custom_item)
async def custom_item_input(message: types.Message, state: FSMContext):
    asyncio.create_task(delete_after_delay(message.chat.id, message.message_id))
    await state.update_data(item=message.text)
    msg = await message.answer(f"'{message.text}' үшін сомманы енгізіңіз:")
    await state.set_state(ExpenseForm.waiting_for_amount)
    asyncio.create_task(delete_after_delay(message.chat.id, msg.message_id))

@dp.message(ExpenseForm.waiting_for_amount)
async def amount_input(message: types.Message, state: FSMContext):
    asyncio.create_task(delete_after_delay(message.chat.id, message.message_id))
    try:
        amount = float(message.text)
        await state.update_data(amount=amount)
        msg = await message.answer("Төлем түрін таңдаңыз:", reply_markup=payment_menu())
        asyncio.create_task(delete_after_delay(message.chat.id, msg.message_id))
    except ValueError:
        msg = await message.answer("Қате! Тек сан енгізіңіз:")
        asyncio.create_task(delete_after_delay(message.chat.id, msg.message_id))

@dp.callback_query(F.data.startswith("pay_"))
async def process_payment(callback: types.CallbackQuery, state: FSMContext):
    pay = callback.data.split("_")[1]
    if pay == "custom":
        msg = await callback.message.answer("Төлем түрін өзіңіз жазыңыз:")
        await state.set_state(ExpenseForm.waiting_for_custom_payment)
        asyncio.create_task(delete_after_delay(callback.message.chat.id, msg.message_id))
    else:
        await save_expense(callback.message, state, pay)
    await callback.answer()

@dp.message(ExpenseForm.waiting_for_custom_payment)
async def custom_payment_input(message: types.Message, state: FSMContext):
    asyncio.create_task(delete_after_delay(message.chat.id, message.message_id))
    await save_expense(message, state, message.text)

async def save_expense(message: types.Message, state: FSMContext, payment_method: str):
    data = await state.get_data()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute(
        "INSERT INTO expenses (user_id, date, category, item, amount, payment_method) VALUES (?, ?, ?, ?, ?, ?)",
        (message.chat.id, today_str, data['category'], data['item'], data['amount'], payment_method)
    )
    conn.commit()
    
    msg = await message.answer(f"✅ Сақталды!\nТауар: {data['item']}\nСумма: {data['amount']} ₸\nТөлем: {payment_method}")
    asyncio.create_task(delete_after_delay(message.chat.id, msg.message_id))
    await state.clear()

# --- БҮГІНГІ ШЫҒЫНДАР (Тұрақты қалады, өшпейді) ---
@dp.callback_query(F.data == "today_expenses")
async def today_expenses_report(callback: types.CallbackQuery):
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT item, amount, payment_method FROM expenses WHERE date = ?", (today_str,))
    rows = cursor.fetchall()
    
    if not rows:
        await callback.message.answer(f"📅 {today_str} күніне шығындар табылмады.")
        await callback.answer()
        return

    text = f"📅 **Бүгінгі шығындар ({today_str}):**\n\n"
    pay_totals = {}
    total_day = 0
    
    for row in rows:
        item, amt, pay = row
        text += f"▪️ {item}: {amt} ₸ ({pay})\n"
        pay_totals[pay] = pay_totals.get(pay, 0) + amt
        total_day += amt
        
    text += "\n💳 **Төлем түрлері бойынша:**\n"
    for pay, amt in pay_totals.items():
        text += f" - {pay}: {amt} ₸\n"
        
    text += f"\n💰 **Жалпы бүгінгі шығын:** {total_day} ₸"
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# --- 1 АЙЛЫҚ ШЫҒЫН ---
@dp.callback_query(F.data == "month_expenses")
async def month_expenses_menu(callback: types.CallbackQuery):
    msg = await callback.message.answer("1 айлық шығын түрін таңдаңыз:", reply_markup=report_type_menu("month"))
    asyncio.create_task(delete_after_delay(callback.message.chat.id, msg.message_id))
    await callback.answer()

@dp.callback_query(F.data.startswith("month_"))
async def process_month_report(callback: types.CallbackQuery):
    rep_type = callback.data.split("_")[1]
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if rep_type == "total":
        cursor.execute("SELECT payment_method, SUM(amount) FROM expenses WHERE date BETWEEN ? AND ? GROUP BY payment_method", (start_date, today_str))
        rows = cursor.fetchall()
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE date BETWEEN ? AND ?", (start_date, today_str))
        total_sum = cursor.fetchone()[0] or 0
        
        text = f"📊 **1 айлық Жалпы шығындар ({start_date} / {today_str}):**\n\n"
        for row in rows:
            text += f"💳 {row[0]}: {row[1]} ₸\n"
        text += f"\n💰 **Жалпы 1 айлық сомма:** {total_sum} ₸"
        
    else: # detail
        cursor.execute("SELECT item, SUM(amount) FROM expenses WHERE date BETWEEN ? AND ? GROUP BY item", (start_date, today_str))
        rows = cursor.fetchall()
        text = f"🔍 **1 айлық Жеке-жеке шығындар:**\n\n"
        for row in rows:
            text += f"▪️ {row[0]}: {row[1]} ₸\n"
            
    msg = await callback.message.answer(text, parse_mode="Markdown")
    asyncio.create_task(delete_after_delay(callback.message.chat.id, msg.message_id))
    await callback.answer()

# --- БЕЛГІЛЕНГЕН МЕРЗІМ ШЫҒЫНЫ ---
@dp.callback_query(F.data == "period_expenses")
async def period_expenses_start(callback: types.CallbackQuery, state: FSMContext):
    msg = await callback.message.answer("Бастапқы датаны енгізіңіз (ЖЖЖЖ-ЖЖ-КК, мысалы: 2026-06-01):")
    await state.set_state(ExpenseForm.waiting_for_period_start)
    asyncio.create_task(delete_after_delay(callback.message.chat.id, msg.message_id))
    await callback.answer()

@dp.message(ExpenseForm.waiting_for_period_start)
async def period_start_input(message: types.Message, state: FSMContext):
    asyncio.create_task(delete_after_delay(message.chat.id, message.message_id))
    await state.update_data(start_date=message.text)
    msg = await message.answer("Соңғы датаны енгізіңіз (ЖЖЖЖ-ЖЖ-КК, мысалы: 2026-06-23):")
    await state.set_state(ExpenseForm.waiting_for_period_end)
    asyncio.create_task(delete_after_delay(message.chat.id, msg.message_id))

@dp.message(ExpenseForm.waiting_for_period_end)
async def period_end_input(message: types.Message, state: FSMContext):
    asyncio.create_task(delete_after_delay(message.chat.id, message.message_id))
    await state.update_data(end_date=message.text)
    msg = await message.answer("Шығын есебінің түрін таңдаңыз:", reply_markup=report_type_menu("period"))
    asyncio.create_task(delete_after_delay(message.chat.id, msg.message_id))

@dp.callback_query(F.data.startswith("period_"))
async def process_period_report(callback: types.CallbackQuery, state: FSMContext):
    rep_type = callback.data.split("_")[1]
    state_data = await state.get_data()
    start_date = state_data.get('start_date')
    end_date = state_data.get('end_date')
    
    if rep_type == "total":
        cursor.execute("SELECT payment_method, SUM(amount) FROM expenses WHERE date BETWEEN ? AND ? GROUP BY payment_method", (start_date, end_date))
        rows = cursor.fetchall()
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE date BETWEEN ? AND ?", (start_date, end_date))
        total_sum = cursor.fetchone()[0] or 0
        
        text = f"📊 **Мерзімдік Жалпы шығындар ({start_date} - {end_date}):**\n\n"
        for row in rows:
            text += f"💳 {row[0]}: {row[1]} ₸\n"
        text += f"\n💰 **Жалпы сомма:** {total_sum} ₸"
        
    else: # detail
        cursor.execute("SELECT item, SUM(amount) FROM expenses WHERE date BETWEEN ? AND ? GROUP BY item", (start_date, end_date))
        rows = cursor.fetchall()
        text = f"🔍 **Мерзімдік Жеке-жеке шығындар ({start_date} - {end_date}):**\n\n"
        for row in rows:
            text += f"▪️ {row[0]}: {row[1]} ₸\n"
            
    msg = await callback.message.answer(text, parse_mode="Markdown")
    asyncio.create_task(delete_after_delay(callback.message.chat.id, msg.message_id))
    await state.clear()
    await callback.answer()

# --- БОТТЫ ІСКЕ ҚОСУ ---
import asyncio

async def main():
    # Ескі кезекте тұрған хабарламаларды тазалау
    await bot.delete_webhook(drop_pending_updates=True)
    # Ботты қосу
    await dp.start_polling(bot, handle_signals=False)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот тоқтатылды")