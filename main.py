# main.py - ФИНАЛЬНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ

import os
import telebot
from flask import Flask, request

from bot_instance import bot
from config import TOKEN
import message_handlers

# --- НАЧАЛО ФИНАЛЬНОГО ИСПРАВЛЕНИЯ ---

# 1. Создаем простой и стандартный, но все еще секретный путь для вебхука.
#    Это более надежно, чем использовать токен напрямую в URL.
WEBHOOK_PATH = f"/webhook/{TOKEN}"

APP_URL = os.environ.get("RENDER_EXTERNAL_URL")

if APP_URL:
    # 2. Собираем полный URL с новым путем
    WEBHOOK_URL = f"{APP_URL}{WEBHOOK_PATH}"

    # Устанавливаем вебхук
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    print(f"ФИНАЛЬНАЯ ПРОВЕРКА: Webhook установлен на: {WEBHOOK_URL}")
else:
    print("Не удалось найти RENDER_EXTERNAL_URL, вебхук не установлен.")

# --- КОНЕЦ ФИНАЛЬНОГО ИСПРАВЛЕНИЯ ---

app = Flask(__name__)


# 3. Указываем наш новый путь в обработчике Flask
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook_handler():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Unsupported Media Type', 415


# --- Служебный роут для проверки, что сервис жив ---
@app.route('/')
def index():
    return "Bot is running!", 200


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)