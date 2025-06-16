# bot_instance.py
import telebot
from config import TOKEN

bot = telebot.TeleBot(TOKEN, parse_mode='Markdown') # parse_mode по умолчанию для удобства
admin_action_prompts = {} # {chat_id: {'action': 'имя_действия', 'order_id': id_заказа, 'data': {}}}

print("Экземпляр бота создан (bot_instance.py)")