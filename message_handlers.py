# message_handlers.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
from bot_instance import bot
import client_handlers
import admin_handlers
import data_manager
from datetime import datetime
from config import ADMIN_GROUP_ID, TEXTS


# ==========================================================
# --- РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ (КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ) ---
# ==========================================================

@bot.message_handler(commands=['start', 'help'])
def handle_start_command(message):
    """ Эта функция ловит команду /start и вызывает вашу логику из client_handlers. """
    print(f"Получена команда /start от {message.chat.id}")
    client_handlers.send_welcome(message, bot)


@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    """ Эта функция ловит АБСОЛЮТНО ВСЕ нажатия на кнопки и решает, куда их направить. """
    print(f"Получен callback: {call.data} от {call.message.chat.id}")
    if 'admin' in call.data:
        if 'cafe' in call.data:
            admin_handlers.handle_admin_cafe_status_callbacks(call, bot)
        elif 'broadcast' in call.data:
            admin_handlers.handle_broadcast_callbacks(call, bot)
        else:
            admin_handlers.handle_admin_order_callbacks(call, bot)
    else:
        action = call.data.split('_')[0]
        if action == 'main':
            client_handlers.handle_main_menu_callback(call, bot)
        elif action == 'cat':
            client_handlers.handle_category_selection(call, bot)
        elif action == 'item':
            client_handlers.handle_item_selection(call, bot)
        elif action == 'cart':
            client_handlers.handle_cart_action(call, bot)
        elif action == 'order':
            client_handlers.handle_order_confirmation_flow(call, bot)
        elif call.data.startswith('client_comment'):
            client_handlers.handle_client_comment_prompt(call, bot)
        elif call.data.startswith('client_delivery_confirmed'):
            client_handlers.handle_client_confirm_delivery(call, bot)
        elif action in ['to', 'preorder']:
            client_handlers.handle_navigation_callbacks(call, bot)
        else:
            print(f"Неизвестный клиентский callback: {call.data}")


@bot.message_handler(content_types=['photo'])
def handle_photo_router(message):
    """ Эта функция ловит любое фото и отдает его вашей функции handle_photo_messages. """
    handle_photo_messages(message, bot)


@bot.message_handler(content_types=['text'])
def handle_text_router(message):
    """ Эта функция ловит любой текст и отдает его вашей функции handle_text_messages. """
    handle_text_messages(message, bot)


# ==========================================================
# --- ВАШ СУЩЕСТВУЮЩИЙ КОД ДЛЯ ОБРАБОТКИ ЛОГИКИ ---
# ==========================================================

def handle_text_messages(message, bot_obj):
    # (Эта функция остается такой же, как в вашем файле)
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.strip()
    user_session = data_manager.get_user_session_data(chat_id)
    current_state = user_session.get('state')

    # ... (весь остальной код вашей функции handle_text_messages без изменений) ...
    # Я не буду его копировать сюда, чтобы не загромождать ответ.
    # Просто оставьте вашу существующую функцию handle_text_messages здесь.


def handle_photo_messages(message, bot_obj):
    # (Эта функция остается такой же, как в вашем файле)
    chat_id = message.chat.id
    user_session = data_manager.get_user_session_data(chat_id)
    current_state = user_session.get('state')
    order_id = user_session.get('current_order_id')

    if current_state == 'awaiting_payment_photo' and order_id:
        photo_file_id = message.photo[-1].file_id
        admin_handlers.handle_payment_receipt_photo(
            bot_obj=bot_obj, order_id=order_id, client_chat_id=chat_id,
            photo_file_id=photo_file_id, client_message_id_to_update=user_session.get('main_message_id')
        )
    elif message.chat.type == "private":
        bot_obj.send_message(chat_id, "Я получил ваше фото, но не знаю, что с ним делать сейчас.")


print("Модуль message_handlers.py загружен.")