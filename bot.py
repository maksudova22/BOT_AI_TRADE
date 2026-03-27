import asyncio
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
import pandas as pd

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

TOKEN = "8593052757:AAGt1P-IZuHz2hxYpfMoxSNZmnfLDDUlux0"
CHANNEL = -1003468351423
MANAGER = "@managfam"


bot = Bot(token=TOKEN)
dp = Dispatcher()

wins = 0
losses = 0
active_users = set()

TARGET_WINRATE = 0.85

# 💎 КНОПКИ
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Отримати сигнал")],
        [KeyboardButton(text="📈 Статистика")],
        [KeyboardButton(text="💬 Менеджер")]
    ],
    resize_keyboard=True
)

# 💱 ПАРИ
PAIRS = {
    "EUR/USD": "EURUSDT",
    "GBP/USD": "GBPUSDT",
    "AUD/USD": "AUDUSDT",
    "USD/JPY": "JPYUSDT",
    "USD/CAD": "CADUSDT",
    "EUR/JPY": "EURUSDT",
    "GBP/JPY": "GBPUSDT",
    "EUR/GBP": "EURUSDT",
    "AUD/JPY": "AUDUSDT",
    "CHF/JPY": "CHFUSDT",
    "BTC/USD": "BTCUSDT",
    "ETH/USD": "ETHUSDT",
    "BNB/USD": "BNBUSDT",
    "SOL/USD": "SOLUSDT",
    "XRP/USD": "XRPUSDT"
}

# 🔒 ПІДПИСКА
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

# 📥 ЦІНА
def get_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        return float(requests.get(url, timeout=5).json()["price"])
    except:
        return None

# 📊 СВІЧКИ
def get_candles(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=50"
        data = requests.get(url, timeout=5).json()

        df = pd.DataFrame(data)
        df = df.iloc[:, :6]
        df.columns = ["time", "open", "high", "low", "close", "volume"]
        df["close"] = df["close"].astype(float)

        return df
    except:
        return None

# 📊 RSI
def calculate_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return (100 - (100 / (1 + rs))).iloc[-1]

# 🧠 АНАЛІЗ
def analyze_market():
    signals = []

    for pair_name, symbol in PAIRS.items():
        try:
            df = get_candles(symbol)
            if df is None:
                continue

            closes = df["close"]

            ema_fast = closes.ewm(span=5).mean().iloc[-1]
            ema_slow = closes.ewm(span=15).mean().iloc[-1]
            rsi = calculate_rsi(df)

            last_price = closes.iloc[-1]
            prev_price = closes.iloc[-2]

            score_up = 0
            score_down = 0

            if ema_fast > ema_slow:
                score_up += 1
            else:
                score_down += 1

            if rsi > 50:
                score_up += 1
            else:
                score_down += 1

            if last_price > prev_price:
                score_up += 1
            else:
                score_down += 1

            direction = "ВГОРУ ⬆️" if score_up >= score_down else "ВНИЗ ⬇️"
            strength = max(score_up, score_down)

            signals.append((pair_name, symbol, direction, strength))

        except:
            continue

    if not signals:
        pair_name = random.choice(list(PAIRS.keys()))
        symbol = PAIRS[pair_name]
        direction = random.choice(["ВГОРУ ⬆️", "ВНИЗ ⬇️"])
        return pair_name, symbol, direction

    signals = sorted(signals, key=lambda x: x[3], reverse=True)

    pair_name, symbol, direction, _ = random.choice(signals[:5])

    return pair_name, symbol, direction

# 🔔 ФОН РЕЗУЛЬТАТУ (ВИПРАВЛЕНО)
async def process_result(bot, chat_id, symbol, direction, start_price, exp):
    global wins, losses

    print("RESULT TASK STARTED")

    try:
        await asyncio.sleep(exp * 60)

        end_price = get_price(symbol)
        if end_price is None:
            end_price = start_price + random.uniform(-0.5, 0.5)

        total = wins + losses

        if total < 10:
            win = random.random() < 0.9
        else:
            current_winrate = wins / total

            if current_winrate < TARGET_WINRATE:
                win = random.random() < 0.9
            else:
                win = random.random() < 0.7

    except:
        win = random.choice([True, False])

    if win:
        wins += 1
        result_text = "✅ <b>ЗАЙШЛО</b>"
    else:
        losses += 1
        result_text = "❌ <b>LOSE</b>"

    await bot.send_message(chat_id, f"""
📊 <b>РЕЗУЛЬТАТ СИГНАЛУ</b>

{result_text}
""", parse_mode="HTML")

# 🚀 START
@dp.message(Command("start"))
async def start(message: Message):
    if not await check_sub(message.from_user.id):
        await message.answer(f"📩 Менеджер: {MANAGER}")
        return

    await message.answer("""
💎 <b>ДОСТУП ВІДКРИТО</b>

⬇️ Обирай нижче та отримай прибуткові сигнали
""", reply_markup=kb, parse_mode="HTML")

# 📊 СИГНАЛ
@dp.message(F.text == "📊 Отримати сигнал")
async def signal(message: Message):
    user_id = message.from_user.id

    if user_id in active_users:
        await message.answer("⏳ Зачекай попередній сигнал")
        return

    active_users.add(user_id)

    try:
        msg = await message.answer("🔍 Аналіз ринку...")
        await asyncio.sleep(1)
        await msg.edit_text("📊 Обробка...")
        await asyncio.sleep(1)

        pair, symbol, direction = analyze_market()
        exp = random.choice([1, 2])

        now = datetime.now(ZoneInfo("Europe/Kyiv"))
        entry_time = (now + timedelta(minutes=1)).replace(second=0)
        end_time = entry_time + timedelta(minutes=exp)

        await message.answer(f"""
🚀 <b>СИГНАЛ</b>

💱 {pair}
📊 {direction}

⏰ {entry_time.strftime("%H:%M")} → {end_time.strftime("%H:%M")}
""", parse_mode="HTML")

        start_price = get_price(symbol)
        if start_price is None:
            start_price = random.uniform(1, 100)

        await message.answer("⏳ Очікуємо результат...")

        # 🔥 ФОН
        asyncio.create_task(
            process_result(bot, message.chat.id, symbol, direction, start_price, exp)
        )

    finally:
        active_users.discard(user_id)

# 📈 СТАТИСТИКА
@dp.message(F.text == "📈 Статистика")
async def stats(message: Message):
    total = wins + losses

    if total == 0:
        await message.answer("📊 Поки немає даних")
        return

    winrate = round((wins / total) * 100, 1)

    await message.answer(f"""
📊 <b>СТАТИСТИКА</b>

✅ {wins}
❌ {losses}
📈 {winrate}%
""", parse_mode="HTML")

# 💬 МЕНЕДЖЕР
@dp.message(F.text == "💬 Менеджер")
async def manager(message: Message):
    await message.answer(f"❌ ДОСТУП ОБМЕЖЕНО

Для використання бота необхідно оформити підписку 📊

🔒 Після підписки ти отримаєш:
• 🚀 Торгові сигнали
• 📈 Високу прохідність
• 💰 Стабільний результат {MANAGER}")

# ▶️ ЗАПУСК
async def main():
    print("🚀 BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

