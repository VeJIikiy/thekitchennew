# main.py (с СЕКРЕТНОЙ СТРАНИЦЕЙ ДЛЯ ПРОВЕРКИ ВЕБХУКА)

import os
import telebot
from flask import Flask, request
import logging
import time
from datetime import datetime

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from bot_instance import bot
from config import TOKEN
import message_handlers

# Установка вебхука при старте (остается без изменений)
WEBHOOK_PATH = f"/webhook/{TOKEN}"
APP_URL = os.environ.get("RENDER_EXTERNAL_URL")
if APP_URL:
    WEBHOOK_URL = f"{APP_URL}{WEBHOOK_PATH}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    logging.info(f"Webhook УСТАНОВЛЕН на: {WEBHOOK_URL}")

app = Flask(__name__)

# Обработчик запросов от Telegram (остается без изменений)
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook_handler():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

# --- НАЧАЛО НОВОГО ДИАГНОСТИЧЕСКОГО КОДА ---
# Этот секретный адрес будет в реальном времени показывать текущий статус вебхука
@app.route('/get_webhook_status_debug_12345')
def get_webhook_status_route():
    try:
        webhook_info = bot.get_webhook_info()
        info_str = (
            "---!!! РУЧНАЯ ПРОВЕРКА СТАТУСА ВЕБХУКА !!!---\n"
            f"URL: {webhook_info.url}\n"
            f"Ожидающие обновления: {webhook_info.pending_update_count}\n"
            f"Дата последней ошибки: {datetime.fromtimestamp(webhook_info.last_error_date) if webhook_info.last_error_date else 'Ошибок не было'}\n"
            f"Сообщение последней ошибки: {webhook_info.last_error_message}\n"
            "---!!! КОНЕЦ ИНФОРМАЦИИ !!!---"
        )
        logging.info(info_str)
        # Возвращаем информацию прямо в браузер для удобства
        return f"<pre>{info_str}</pre>", 200
    except Exception as e:
        logging.exception("!!! НЕ УДАЛОСЬ ПОЛУЧИТЬ ИНФОРМАЦИЮ О ВЕБХУКЕ (РУЧНАЯ ПРОВЕРКА) !!!")
        return "Ошибка получения информации о вебхуке.", 500
# --- КОНЕЦ НОВОГО ДИАГНОСТИЧЕСКОГО КОДА ---

# Служебный роут (остается без изменений)
@app.route('/')
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)