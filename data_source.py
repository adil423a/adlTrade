"""
Получение свечей (OHLC) с Twelve Data.
Бесплатный тариф: https://twelvedata.com/pricing (800 запросов/день хватит с головой
для ручных проверок по команде).

Получить API-ключ: https://twelvedata.com/ → Sign up → Dashboard → API Key
"""

import os
import requests
from analysis import Candle

TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY")
BASE_URL = "https://api.twelvedata.com/time_series"


def fetch_candles(symbol: str, interval: str = "1h", outputsize: int = 60) -> list[Candle]:
    """
    symbol: например "EUR/USD"
    interval: "1min","5min","15min","1h","4h","1day" и т.д.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": TWELVE_DATA_API_KEY,
        "format": "JSON",
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    data = resp.json()

    if data.get("status") == "error" or "values" not in data:
        raise RuntimeError(f"Twelve Data API error: {data.get('message', data)}")

    values = data["values"]
    values.reverse()  # API отдаёт от новых к старым — разворачиваем в хронологический порядок

    candles = [
        Candle(
            time=v["datetime"],
            open=float(v["open"]),
            high=float(v["high"]),
            low=float(v["low"]),
            close=float(v["close"]),
        )
        for v in values
    ]
    return candles
