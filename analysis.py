"""
Логика анализа графика:
- поиск уровней поддержки/сопротивления по локальным хаям/лоям
- определение базовых свечных паттернов
- формирование рекомендации (BUY / SELL / WAIT) с обоснованием

Это ОТПРАВНАЯ ТОЧКА. Правила упрощены и их обязательно нужно
подстроить под твою реальную торговую систему.
"""

from dataclasses import dataclass


@dataclass
class Candle:
    time: str
    open: float
    high: float
    low: float
    close: float

    @property
    def body(self):
        return abs(self.close - self.open)

    @property
    def range(self):
        return self.high - self.low

    @property
    def is_bullish(self):
        return self.close > self.open

    @property
    def upper_wick(self):
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self):
        return min(self.open, self.close) - self.low


def find_support_resistance(candles: list[Candle], lookback: int = 3, max_levels: int = 4):
    """
    Ищет локальные экстремумы (свинг-хай/свинг-лоу) — свечу, у которой
    high/low выше/ниже, чем у `lookback` свечей слева и справа.
    Возвращает списки уровней поддержки и сопротивления, отсортированные
    по близости к последней цене.
    """
    highs, lows = [], []
    n = len(candles)

    for i in range(lookback, n - lookback):
        window = candles[i - lookback: i + lookback + 1]
        c = candles[i]

        if c.high == max(w.high for w in window):
            highs.append(c.high)
        if c.low == min(w.low for w in window):
            lows.append(c.low)

    last_price = candles[-1].close

    # убираем дубли и слишком близкие уровни
    def dedupe(levels, price):
        levels = sorted(set(round(l, 5) for l in levels))
        cleaned = []
        for l in levels:
            if not cleaned or abs(l - cleaned[-1]) / price > 0.0008:  # ~8 пипсов на паре ~1.0
                cleaned.append(l)
        return cleaned

    resistance = [l for l in dedupe(highs, last_price) if l > last_price]
    support = [l for l in dedupe(lows, last_price) if l < last_price]

    resistance = sorted(resistance)[:max_levels]
    support = sorted(support, reverse=True)[:max_levels]

    return support, resistance


def detect_pattern(candles: list[Candle]):
    """
    Проверяет последнюю свечу (и предыдущую, если нужно) на базовые паттерны:
    бычье/медвежье поглощение, пин-бар (молот/падающая звезда), доджи.
    Возвращает (название_паттерна, направление) или (None, None).
    """
    if len(candles) < 2:
        return None, None

    prev, last = candles[-2], candles[-1]

    # Поглощение
    if (
        last.is_bullish and not prev.is_bullish
        and last.close >= prev.open and last.open <= prev.close
    ):
        return "Бычье поглощение", "BUY"

    if (
        not last.is_bullish and prev.is_bullish
        and last.open >= prev.close and last.close <= prev.open
    ):
        return "Медвежье поглощение", "SELL"

    # Пин-бар / молот (длинная нижняя тень)
    if last.range > 0 and last.lower_wick / last.range > 0.6 and last.body / last.range < 0.3:
        return "Пин-бар (молот)", "BUY"

    # Падающая звезда (длинная верхняя тень)
    if last.range > 0 and last.upper_wick / last.range > 0.6 and last.body / last.range < 0.3:
        return "Пин-бар (падающая звезда)", "SELL"

    # Доджи — нерешительность, не даёт направленного сигнала
    if last.range > 0 and last.body / last.range < 0.1:
        return "Доджи", None

    return None, None


def build_signal(candles: list[Candle]):
    """
    Главная функция: собирает уровни + паттерн последней свечи
    и решает, есть ли сигнал рядом с уровнем.

    Логика (упрощённая, замени на свою):
    сигнал считается валидным, если паттерн подтверждающий и
    последняя цена находится близко (< 0.15%) к уровню поддержки/сопротивления.
    """
    support, resistance = find_support_resistance(candles)
    pattern, direction = detect_pattern(candles)
    last_price = candles[-1].close

    def nearest(levels):
        if not levels:
            return None
        return min(levels, key=lambda l: abs(l - last_price))

    near_support = nearest(support)
    near_resistance = nearest(resistance)

    near_level = None
    level_type = None
    if near_support and abs(last_price - near_support) / last_price < 0.0015:
        near_level, level_type = near_support, "поддержка"
    elif near_resistance and abs(last_price - near_resistance) / last_price < 0.0015:
        near_level, level_type = near_resistance, "сопротивление"

    signal = "WAIT"
    reason_lines = []

    if pattern:
        reason_lines.append(f"Паттерн последней свечи: {pattern}")
    else:
        reason_lines.append("Явного свечного паттерна не найдено")

    if near_level:
        reason_lines.append(f"Цена вблизи уровня {level_type}: {near_level:.5f}")
        if direction == "BUY" and level_type == "поддержка":
            signal = "BUY"
        elif direction == "SELL" and level_type == "сопротивление":
            signal = "SELL"
    else:
        reason_lines.append("Цена не находится вблизи значимого уровня")

    return {
        "signal": signal,
        "price": last_price,
        "support": support,
        "resistance": resistance,
        "pattern": pattern,
        "reasons": reason_lines,
    }
