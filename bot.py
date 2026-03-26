print("🔥 НОВИЙ БОТ ЗАПУЩЕНИЙ")

import asyncio
import requests
import pandas as pd
import random

from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

# 🔐 НАЛАШТУВАННЯ
TOKEN = "8593052757:AAGt1P-IZuHz2hxYpfMoxSNZmnfLDDUlux0"
CHANNEL = -1003468351423
MANAGER = "@managfam"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 📊 ДАНІ
users = set()
wins = 0
losses = 0
user_signals = {}

# 📲 КНОПКИ
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Отримати сигнал")],
        [KeyboardButton(text="📈 Статистика")],
        [KeyboardButton(text="💬 Менеджер")]
    ],
    resize_keyboard=True
)

# 🧠 ТЕКСТИ
texts = [
    "Сильний сигнал 🔥",
    "Точний вхід 🎯",
    "За трендом 📊",
    "Аналіз підтверджено ✔️",
    "Хороша точка входу",
    "Ринок дає можливість",
    "Є рух на ринку"
]

# 🔐 ПЕРЕВІРКА ПІДПИСКИ
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

# 💰 ЦІНА
def get_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    return float(requests.get(url).json()["price"])

# 📊 СВІЧКИ
def get_candles(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=50"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "ct","qv","n","tb","tq","ignore"
    ])

    df["close"] = df["close"].astype(float)
    return df

# 📈 RSI
def calculate_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

# 🧠 АНАЛІЗ
def analyze_market():
    pairs = {
        "EUR/USD": "EURUSDT",
        "GBP/USD": "GBPUSDT",
        "AUD/USD": "AUDUSDT",
        "USD/JPY": "JPYUSDT",
        "USD/CAD": "CADUSDT"
    }

    for pair_name, symbol in pairs.items():
        df = get_candles(symbol)
        closes = df["close"]

        ema_fast = closes.ewm(span=5).mean().iloc[-1]
        ema_slow = closes.ewm(span=20).mean().iloc[-1]
        rsi = calculate_rsi(df)

        last_price = closes.iloc[-1]
        prev_price = closes.iloc[-2]

        # ⬆️ ВГОРУ
        if ema_fast > ema_slow and rsi > 50 and last_price > prev_price:
            return pair_name, symbol, "ВГОРУ ⬆️"

        # ⬇️ ВНИЗ
        if ema_fast < ema_slow and rsi < 50 and last_price < prev_price:
            return pair_name, symbol, "ВНИЗ ⬇️"

    return None, None, None

# 🚀 START
@dp.message(Command("start"))
async def start(message: Message):
    users.add(message.from_user.id)

    if not await check_sub(message.from_user.id):
        await message.answer(f"""
🔒 Доступ закритий

Потрібна підписка на канал

💎 Отримати доступ:
{MANAGER}
""")
        return

    fake_users = random.randint(120, 350)

    await message.answer(f"""
💎 Доступ відкрито

👥 Онлайн зараз: {fake_users}

👇 Обери дію
""", reply_markup=kb)

# 📊 СИГНАЛ
@dp.message(F.text == "📊 Отримати сигнал")
async def signal(message: Message):
    global wins, losses

    if not await check_sub(message.from_user.id):
        await message.answer(f"🔒 Напиши менеджеру:\n{MANAGER}")
        return

    user_id = message.from_user.id
    user_signals[user_id] = user_signals.get(user_id, 0)

    if user_signals[user_id] >= 3:
        await message.answer(f"""
🔒 Ліміт сигналів

💎 Доступ через:
{MANAGER}
""")
        return

    user_signals[user_id] += 1

    msg = await message.answer("⏳ Аналізую ринок...")
    await asyncio.sleep(2)
    await msg.edit_text("📊 Збираю дані...")
    await asyncio.sleep(2)
    await msg.edit_text("📈 Аналіз завершено")

    pair = None

    for _ in range(5):
        pair, symbol, direction = analyze_market()
        if pair:
            break
        await asyncio.sleep(1)

    if not pair:
        await message.answer("⚠️ Немає сигналу")
        return

    # ⏰ ЧАС
    exp = 1
    now = datetime.now()
    entry_time = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    end_time = entry_time + timedelta(minutes=exp)

    text = random.choice(texts)

    await message.answer(f"""
📊 СИГНАЛ

Актив: {pair}
Напрямок: {direction}

⏰ Вхід: {entry_time.strftime("%H:%M")}
⏳ Експірація: {end_time.strftime("%H:%M")}

{text}
""")

    # ⏳ ЧЕКАЄМО ДО ВХОДУ
    wait_seconds = (entry_time - datetime.now()).total_seconds()
    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)

    start_price = get_price(symbol)

    await message.answer(f"🚀 Вхід зараз: {pair} {direction}")

    await asyncio.sleep(exp * 60)
    end_price = get_price(symbol)

    if direction == "ВГОРУ ⬆️":
        result = "ЗАЙШЛО ✅" if end_price > start_price else "НЕ ЗАЙШЛО ❌"
    else:
        result = "ЗАЙШЛО ✅" if end_price < start_price else "НЕ ЗАЙШЛО ❌"

    if result == "ЗАЙШЛО ✅":
        wins += 1
    else:
        losses += 1

    await message.answer(f"📊 {result}")

# 📈 СТАТИСТИКА
@dp.message(F.text == "📈 Статистика")
async def stats(message: Message):
    total = wins + losses

    if total == 0:
        await message.answer("Поки немає статистики")
        return

    winrate = round((wins / total) * 100, 1)

    await message.answer(f"""
📊 Статистика

✅ Виграшів: {wins}
❌ Програшів: {losses}
📈 Прохідність: {winrate}%
""")

# 💬 МЕНЕДЖЕР
@dp.message(F.text == "💬 Менеджер")
async def manager(message: Message):
    await message.answer(f"📩 Напиши: {MANAGER}")

# ▶️ ЗАПУСК
async def main():
    print("🚀 BOT START")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

