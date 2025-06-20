# main.py - Финальная версия для деплоя на Render

import os
import telebot  # Убедитесь, что telebot импортирован
from flask import Flask, request

# Импортируем экземпляр бота и токен
from bot_instance import bot
from config import TOKEN  # Предполагается, что TOKEN - это строка с вашим токеном

# Импортируем message_handlers.
# Этот файл должен сам импортировать client_handlers и admin_handlers,
# чтобы все декорированные функции (@bot.message_handler) были зарегистрированы.
import message_handlers

# --- НАЧАЛО ИСПРАВЛЕНИЯ ---

# Получаем адрес нашего приложения на Render
APP_URL = os.environ.get("RENDER_EXTERNAL_URL")

# Если мы работаем на Render (адрес существует), то устанавливаем вебхук
if APP_URL:
    # Собираем полный URL для вебхука
    WEBHOOK_URL = f"{APP_URL}/{TOKEN}"

    # Удаляем старый вебхук (на всякий случай)
    bot.remove_webhook()

    # Устанавливаем новый вебхук
    bot.set_webhook(url=WEBHOOK_URL)

    print(f"Webhook установлен на: {WEBHOOK_URL}")  # Это сообщение вы увидите в логах Render
else:
    print("Не удалось найти RENDER_EXTERNAL_URL, вебхук не установлен (возможно, локальный запуск).")

# --- КОНЕЦ ИСПРАВЛЕНИЯ ---


# Создаем экземпляр веб-приложения Flask
app = Flask(__name__)


# --- Основной роут для приема вебхуков от Telegram ---
# Telegram будет отправлять обновления сюда
@app.route('/' + TOKEN, methods=['POST'])
def webhook_handler():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        # Передаем обновление в библиотеку telebot для обработки
        bot.process_new_updates([update])
        # Отвечаем Telegram, что все в порядке
        return '', 200
    else:
        # Если пришел запрос другого типа, возвращаем ошибку
        return 'Unsupported Media Type', 415


# --- Служебный роут для проверки, что сервис жив ---
@app.route('/')
def index():
    return "Bot is running!", 200


if __name__ == "__main__":
    # Render сам задаст нужный порт через переменную окружения PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)