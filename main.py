# main.py
from bot_instance import bot
import client_handlers
import admin_handlers
import message_handlers
import data_manager
from config import ADMIN_GROUP_ID


def is_user_admin_of_group(user_id_to_check):  # Без изменений
    if not ADMIN_GROUP_ID: return False
    try:
        member = bot.get_chat_member(ADMIN_GROUP_ID, user_id_to_check)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False


@bot.message_handler(commands=['start'])  # Без изменений
def handle_start_command(message): client_handlers.send_welcome(message, bot)


@bot.message_handler(commands=['cafe_admin_mode'])  # Без изменений
def handle_cafe_admin_mode_command(message):
    if is_user_admin_of_group(message.from_user.id):
        admin_handlers.send_cafe_status_management_menu(message, bot)
    else:
        bot.reply_to(message, "This command is for administrators only.")


@bot.message_handler(commands=['admin_broadcast'])  # Без изменений
def handle_admin_broadcast_command(message):
    if is_user_admin_of_group(message.from_user.id):
        admin_handlers.prompt_for_broadcast_message(message.from_user.id, bot)
    else:
        bot.reply_to(message, "This command is for administrators only.")


@bot.callback_query_handler(func=lambda call: True)
def all_callbacks_handler(call):
    # Клиентские колбэки
    if call.data.startswith('main_'):
        client_handlers.handle_main_menu_callback(call, bot)
    elif call.data.startswith('cat_') or call.data == "menu_unavailable":
        client_handlers.handle_category_selection(call, bot)
    elif call.data.startswith('item_'):
        client_handlers.handle_item_selection(call, bot)
    elif call.data.startswith('cart_'):
        client_handlers.handle_cart_action(call, bot)
    elif call.data.startswith('order_confirm_'):
        client_handlers.handle_order_confirmation_flow(call, bot)
    elif call.data.startswith('client_comment_'):
        client_handlers.handle_client_comment_prompt(call, bot)
    elif call.data.startswith('preorder_') or call.data == 'to_main_menu' or call.data == 'to_categories':
        client_handlers.handle_navigation_callbacks(call, bot)
    # --- НОВЫЙ КЛИЕНТСКИЙ КОЛЛБЭК ---
    elif call.data.startswith('client_confirm_delivery_'):
        client_handlers.handle_client_confirm_delivery(call, bot)

    # Админские колбэки
    elif call.data.startswith('admin_adj_') or \
            call.data.startswith('admin_payment_') or \
            call.data.startswith('admin_req_payment_') or \
            call.data.startswith('admin_order_') or \
            call.data.startswith('admin_comment_client_') or \
            call.data.startswith('admin_delivering_') or \
            call.data.startswith('admin_completed_') or \
            call.data.startswith('admin_cancel_') or \
            call.data.startswith('admin_refresh_'):
        admin_handlers.handle_admin_order_callbacks(call, bot)
    elif call.data.startswith('admin_cafe_'):
        admin_handlers.handle_admin_cafe_status_callbacks(call, bot)
    elif call.data.startswith('admin_broadcast_'):
        admin_handlers.handle_broadcast_callbacks(call, bot)
    else:
        print(f"Неизвестный callback_data в main.py: {call.data}")
        try:
            bot.answer_callback_query(call.id, "Unknown action.")
        except Exception as e:
            print(f"Ошибка ответа на неизвестный callback: {e}")


@bot.message_handler(content_types=['text'])  # Без изменений
def handle_text(message): message_handlers.handle_text_messages(message, bot)


@bot.message_handler(content_types=['photo'])  # Без изменений
def handle_photo(message): message_handlers.handle_photo_messages(message, bot)


if __name__ == '__main__':  # Без изменений
    print("Инициализация данных перед запуском бота...")
    data_manager.load_all_data()
    print("Запуск бота (main.py)...")
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Критическая ошибка при запуске или работе бота: {e}")
        import traceback

        traceback.print_exc()