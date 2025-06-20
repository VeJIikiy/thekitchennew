# main.py (РЕЖИМ ТОТАЛЬНОЙ ДИАГНОСТИКИ)

import os
import telebot
from flask import Flask, request
import logging  # Импортируем модуль логгирования
import time  # Импортируем модуль времени

# Настраиваем более подробный формат логов
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
    logging.info(f"Webhook установлен на: {WEBHOOK_URL}")
else:
    logging.warning("RENDER_EXTERNAL_URL не найден, вебхук не установлен.")

app = Flask(__name__)


# --- Основной роут для приема вебхуков от Telegram С ОТЛАДКОЙ ---
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook_handler():
    start_time = time.time()
    logging.info("!!! ПОЛУЧЕН ВХОДЯЩИЙ ЗАПРОС ОТ TELEGRAM !!!")
    try:
        if request.headers.get('content-type') == 'application/json':
            logging.info("Content-Type верный (application/json). Читаю данные...")

            json_string = request.get_data().decode('utf-8')
            logging.info(f"ПОЛУЧЕННЫЕ ДАННЫЕ: {json_string}")  # Логируем сами данные

            logging.info("Преобразую данные в объект Update...")
            update = telebot.types.Update.de_json(json_string)

            logging.info("Передаю управление в process_new_updates...")
            bot.process_new_updates([update])

            processing_time = time.time() - start_time
            logging.info(f"ОБРАБОТКА УСПЕШНО ЗАВЕРШЕНА за {processing_time:.4f} секунд.")

            return '', 200
        else:
            logging.error(f"НЕВЕРНЫЙ Content-Type: {request.headers.get('content-type')}")
            return 'Unsupported Media Type', 415
    except Exception as e:
        # Логируем ЛЮБУЮ ошибку, которая произойдет внутри
        logging.exception("!!! ВНУТРИ WEBHOOK HANDLER ПРОИЗОШЛА КРИТИЧЕСКАЯ ОШИБКА !!!")
        return 'Internal Server Error', 500


# --- Служебный роут ---
@app.route('/')
def index():
    return "Bot is running!", 200


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)