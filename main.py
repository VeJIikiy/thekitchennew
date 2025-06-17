# main.py - Финальная версия для деплоя на Render

import os
import telebot
from flask import Flask, request

# Импортируем экземпляр бота и токен
from bot_instance import bot
from config import TOKEN

# Импортируем message_handlers.
# Этот файл должен сам импортировать client_handlers и admin_handlers,
# чтобы все декорированные функции (@bot.message_handler) были зарегистрированы.
import message_handlers

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
# Если открыть https://<адрес-вашего-бота>.onrender.com
# вы увидите это сообщение
@app.route('/')
def index():
    return 'The Kitchen Bot is running!', 200


# Важно: в этом файле не должно быть блока if __name__ == "__main__".
# Запуск приложения на сервере выполняет Gunicorn.