# Trading Journal + Signal Bot

Объединённый бот: твой торговый журнал (aiogram + PostgreSQL) плюс
команда проверки сигналов по ТС (`/check`), которая раньше жила в
отдельном боте.

## Что нового

Добавлена команда:

```
/check ПАРА [таймфрейм]
```

Пример: `/check XAUUSD 1h`

Логика анализа (уровни поддержки/сопротивления + свечные паттерны)
находится в `analysis.py`, получение свечей — в `data_source.py`.
Это те же файлы, что были в отдельном сигнальном боте — просто теперь
подключены как ещё один хэндлер в общем `bot.py`.

Всё остальное (журнал сделок, статистика, календарь, баланс,
скриншоты) работает без изменений — это твой оригинальный код.

## Переменные окружения

Нужно задать в Railway (или .env локально):

- `BOT_TOKEN` — токен твоего Telegram-бота (уже есть, раз журнал работал)
- `DATABASE_URL` — строка подключения к PostgreSQL (уже есть)
- `DB_SSL` — true/false, если нужен SSL для БД (уже было настроено)
- `TWELVE_DATA_API_KEY` — **новая переменная**, нужна для команды `/check`.
  Получить бесплатно на https://twelvedata.com/ (Dashboard → API Key)

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Запуск локально

```bash
export BOT_TOKEN=...
export DATABASE_URL=...
export DB_SSL=false
export TWELVE_DATA_API_KEY=...
python bot.py
```

## Деплой

Так же, как деплоился журнал — просто добавь новую переменную
`TWELVE_DATA_API_KEY` в Variables на Railway и обнови файлы в репозитории
(`bot.py`, `analysis.py`, `data_source.py`, `requirements.txt`).

## Структура

- `bot.py` — весь бот: журнал + сигналы, один процесс, один токен
- `analysis.py` — логика поиска уровней и свечных паттернов
- `data_source.py` — получение свечей через Twelve Data API
- `requirements.txt` — зависимости
