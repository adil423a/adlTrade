"""
Telegram-бот: по команде /check <ПАРА> [таймфрейм] анализирует график
и присылает рекомендацию по твоей ТС (уровни + свечные паттерны).

Пример: /check EURUSD 1h
Если таймфрейм не указан — берётся 1h по умолчанию.
"""

import os
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from data_source import fetch_candles
from analysis import build_signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

VALID_INTERVALS = {"1min", "5min", "15min", "30min", "1h", "4h", "1day"}


def format_symbol(raw: str) -> str:
    """EURUSD -> EUR/USD (Twelve Data ждёт пару через слэш)"""
    raw = raw.upper().replace("/", "")
    if len(raw) == 6:
        return f"{raw[:3]}/{raw[3:]}"
    return raw


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я проверяю график по твоей ТС (уровни + свечные паттерны).\n\n"
        "Команда: /check ПАРА [таймфрейм]\n"
        "Пример: /check EURUSD 1h\n"
        "Таймфреймы: 1min, 5min, 15min, 30min, 1h, 4h, 1day (по умолчанию 1h)"
    )


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи пару, например: /check EURUSD")
        return

    pair_raw = context.args[0]
    interval = context.args[1] if len(context.args) > 1 else "1h"

    if interval not in VALID_INTERVALS:
        await update.message.reply_text(
            f"Неизвестный таймфрейм '{interval}'. Доступные: {', '.join(sorted(VALID_INTERVALS))}"
        )
        return

    symbol = format_symbol(pair_raw)
    await update.message.reply_text(f"Смотрю {symbol} на {interval}...")

    try:
        candles = fetch_candles(symbol, interval=interval)
        result = build_signal(candles)
    except Exception as e:
        logger.exception("Ошибка анализа")
        await update.message.reply_text(f"Не получилось получить данные: {e}")
        return

    signal_emoji = {"BUY": "🟢 BUY", "SELL": "🔴 SELL", "WAIT": "⚪ WAIT"}[result["signal"]]

    lines = [
        f"{symbol} ({interval})",
        f"Цена: {result['price']:.5f}",
        "",
        f"Рекомендация: {signal_emoji}",
        "",
        "Обоснование:",
    ]
    lines += [f"• {r}" for r in result["reasons"]]

    if result["support"]:
        lines.append("")
        lines.append("Ближайшие поддержки: " + ", ".join(f"{l:.5f}" for l in result["support"][:3]))
    if result["resistance"]:
        lines.append("Ближайшие сопротивления: " + ", ".join(f"{l:.5f}" for l in result["resistance"][:3]))

    lines.append("")
    lines.append("⚠️ Это не финансовая рекомендация. Решение и ответственность — твои.")

    await update.message.reply_text("\n".join(lines))


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN в переменных окружения")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))

    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
