from flask import Flask, request
import os

# Этот код не использует библиотеку telebot, только самый базовый веб-сервер
app = Flask(__name__)

# Берем токен из тех же настроек, что и основной бот
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8022174272:AAG1aSjbl9VKA3XaWlerOOABE_qH4bhHiwk')

@app.route('/' + TOKEN, methods=['POST'])
def receive_update():
    print("="*40)
    print("!!! ПОЛУЧЕН ЗАПРОС ОТ TELEGRAM !!!")
    print(request.json)
    print("="*40)
    return "OK", 200

if __name__ == '__main__':
    print("--- Тестовый сервер-пустышка запущен на порту 5000 ---")
    app.run(port=5000)