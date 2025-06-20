# main.py (ФИНАЛЬНАЯ ДИАГНОСТИКА)

import os
import telebot
from flask import Flask, request
import logging
import time
from datetime import datetime # Добавили импорт datetime

# Настраиваем логгирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from bot_instance import bot
from config import TOKEN
import message_handlers

# Создаем путь для вебхука
WEBHOOK_PATH = f"/webhook/{TOKEN}"
APP_URL = os.environ.get("RENDER_EXTERNAL_URL")

# Устанавливаем вебхук
if APP_URL:
    WEBHOOK_URL = f"{APP_URL}{WEBHOOK_PATH}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    logging.info(f"Webhook УСТАНОВЛЕН на: {WEBHOOK_URL}")

    # --- НАЧАЛО ДИАГНОСТИЧЕСКОГО КОДА ---
    time.sleep(2) # Даем Telegram пару секунд на обработку
    try:
        webhook_info = bot.get_webhook_info()
        logging.info("---!!! ИНФОРМАЦИЯ О ВЕБХУКЕ ОТ TELEGRAM !!!---")
        logging.info(f"URL, который видит Telegram: {webhook_info.url}")
        logging.info(f"Количество ожидающих сообщений: {webhook_info.pending_update_count}")
        if webhook_info.last_error_date:
            logging.error(f"Дата последней ошибки: {datetime.fromtimestamp(webhook_info.last_error_date)}")
            logging.error(f"Сообщение последней ошибки: {webhook_info.last_error_message}")
        else:
            logging.info("Последних ошибок доставки нет.")
        logging.info("---!!! КОНЕЦ ИНФОРМАЦИИ !!!---")
    except Exception as e:
        logging.exception("!!! НЕ УДАЛОСЬ ПОЛУЧИТЬ ИНФОРМАЦИЮ О ВЕБХУКЕ !!!")
    # --- КОНЕЦ ДИАГНОСТИЧЕСКОГО КОДА ---

else:
    logging.warning("RENDER_EXTERNAL_URL не найден, вебхук не установлен.")


app = Flask(__name__)

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook_handler():
    #... (остальной код остается без изменений)
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)