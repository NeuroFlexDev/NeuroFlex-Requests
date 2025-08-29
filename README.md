# NeuroFlex Pro Bot

Мультиязычный Telegram-бот (RU/EN) для заявок клиентов/партнёров:
- Анкета (FSM) + загрузка файлов (ТЗ, брифы, скриншоты)
- Хранилище: SQLite (основа) + экспорт CSV/JSON
- Google Sheets (опционально)
- Админ-команды: /export, /files <request_id>
- Калькулятор стоимости: /calc

## Быстрый старт
```bash
cp .env.example .env
# отредактируй .env (BOT_TOKEN, ADMIN_ID, USE_SHEETS, ...)
chmod +x run.sh
./run.sh
```

## Команды

* `/start` — приветствие, выбор языка
* `/form` — анкета с файлами и подтверждением
* `/calc` — предварительная оценка
* `/export` — (админ) выгрузка CSV и JSON
* `/files <request_id>` — (админ) показать вложения заявки

## Google Sheets

1. Включить Sheets/Drive API, создать сервисный аккаунт, скачать JSON → `google_creds.json` в корень.
2. Название таблицы = `GOOGLE_SHEET_NAME` в `.env`. Дать доступ сервисному аккаунту (Редактор).
3. Параметр `USE_SHEETS=true`.