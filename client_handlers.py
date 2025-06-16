# client_handlers.py
import os
from bot_instance import bot
import data_manager
import keyboards
import utils
from config import WELCOME_IMAGE_PATH, TEXTS, ADMIN_GROUP_ID, DEFAULT_TIMEZONE
import gsheet_manager
from datetime import datetime


# --- Утилитарная функция _send_or_edit_main_message ---
def _send_or_edit_main_message(bot_obj, chat_id, text, reply_markup=None, photo_path=None, existing_message_id=None,
                               parse_mode='Markdown', new_message_if_edit_fails=True):
    new_message_obj = None
    if existing_message_id:
        try:
            if photo_path and os.path.exists(photo_path):
                print(
                    f"Попытка отредактировать сообщение {existing_message_id} с новым фото. Удаляем старое и шлем новое.")
                raise Exception("Cannot edit message with new photo, sending new one.")
            new_message_obj = bot_obj.edit_message_text(text, chat_id=chat_id, message_id=existing_message_id,
                                                        reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as e_edit:
            print(f"Не удалось отредактировать сообщение {existing_message_id} (Ошибка: {e_edit}).")
            if new_message_if_edit_fails:
                print("Отправляем новое сообщение взамен.")
                try:
                    bot_obj.delete_message(chat_id=chat_id, message_id=existing_message_id)
                except Exception as e_del:
                    print(f"Не удалось удалить старое сообщение {existing_message_id}: {e_del}")
                if photo_path and os.path.exists(photo_path):
                    with open(photo_path, 'rb') as photo_file:
                        new_message_obj = bot_obj.send_photo(chat_id, photo_file, caption=text,
                                                             reply_markup=reply_markup, parse_mode=parse_mode)
                else:
                    new_message_obj = bot_obj.send_message(chat_id, text, reply_markup=reply_markup,
                                                           parse_mode=parse_mode)
    else:
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo_file:
                new_message_obj = bot_obj.send_photo(chat_id, photo_file, caption=text, reply_markup=reply_markup,
                                                     parse_mode=parse_mode)
        else:
            new_message_obj = bot_obj.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    if new_message_obj: data_manager.update_user_session_data(chat_id, 'main_message_id', new_message_obj.message_id)
    return new_message_obj


# --- Основные обработчики клиента ---
def send_welcome(message, bot_obj):  # message здесь это объект сообщения Telegram
    chat_id = message.chat.id
    user_name = message.from_user.first_name or "Гость"
    user_id = message.from_user.id
    try:
        # Приветствие вызывается и при /start, и после некоторых действий.
        # Обновляем/создаем клиента в GSheet только если есть user_id и user_name
        if user_id and user_name:
            gsheet_manager.find_or_create_client(user_id, user_name, phone_number=None)
    except Exception as e:
        print(f"Ошибка gsheet_manager.find_or_create_client при send_welcome: {e}")

    data_manager.init_user_order_session(chat_id)  # Сбрасываем сессию заказа и обратной связи

    welcome_text = f"Здравствуйте, {utils.escape_markdown(user_name)}! 👋\nДобро пожаловать в кафе The Kitchen\nнаш бот готов принять Ваш заказ\nДОСТАВКА В PLAGOO ОТ 150 тысяч ЗА НАШ СЧЕТ"
    markup = keyboards.main_menu_keyboard()
    user_session = data_manager.get_user_session_data(chat_id)
    existing_main_msg_id = user_session.get('main_message_id')

    # Удаляем предыдущее сообщение главного меню, если оно было, чтобы избежать дублирования
    if existing_main_msg_id:
        try:
            bot_obj.delete_message(chat_id, existing_main_msg_id)
        except Exception:  # Если не удалось удалить, не страшно, отправим новое
            pass

    new_msg = _send_or_edit_main_message(bot_obj, chat_id, welcome_text,
                                         reply_markup=markup,
                                         photo_path=WELCOME_IMAGE_PATH,
                                         existing_message_id=None,  # Всегда отправляем новое приветствие
                                         new_message_if_edit_fails=True)
    if new_msg:  # Сохраняем ID нового главного сообщения
        data_manager.update_user_session_data(chat_id, 'main_message_id', new_msg.message_id)
    print(f"Отправлено приветствие с главным меню пользователю {user_name} (ID: {chat_id})")


def handle_main_menu_callback(call, bot_obj):
    chat_id = call.message.chat.id;
    user_session = data_manager.get_user_session_data(chat_id)
    # Используем call.message.message_id как ID сообщения для редактирования, если main_message_id не найден
    message_id = user_session.get('main_message_id') if user_session.get('main_message_id') else call.message.message_id
    user_name = call.from_user.first_name or "Гость";
    user_id = call.from_user.id
    try:
        bot_obj.answer_callback_query(call.id)
    except Exception as e_ans:
        print(f"Ошибка ответа на callback_query (main_menu {call.data}): {e_ans}")

    if call.data == "main_make_order":
        status_details = utils.get_cafe_operational_status_details()
        if not status_details['is_open']:
            text = f"{status_details['status_line']}\n{status_details['schedule_text']}\n\n{TEXTS.get('cafe_closed_can_preorder', 'Кафе закрыто. Хотите оформить предзаказ?')}"
            markup = keyboards.confirm_action_keyboard("preorder_yes", "preorder_no", "Да, оформить предзаказ",
                                                       "Нет, спасибо")
            _send_or_edit_main_message(bot_obj, chat_id, text, reply_markup=markup, existing_message_id=message_id);
            return
        start_new_order_process(chat_id, user_id, user_name, bot_obj, message_id)
    elif call.data == "main_cafe_status":
        status_details = utils.get_cafe_operational_status_details()
        text_to_send = status_details['status_line'] + status_details['schedule_text']
        _send_or_edit_main_message(bot_obj, chat_id, text_to_send, reply_markup=keyboards.main_menu_keyboard(),
                                   existing_message_id=message_id)
    elif call.data == "main_feedback":
        data_manager.update_user_session_data(chat_id, 'feedback_info', {})
        data_manager.update_user_session_data(chat_id, 'state', 'awaiting_feedback_name')
        prompt_text = TEXTS.get("feedback_prompt_name", "Пожалуйста, введите ваше имя (как к вам обращаться):")
        _send_or_edit_main_message(bot_obj, chat_id, prompt_text,
                                   reply_markup=keyboards.back_to_main_menu_keyboard(),
                                   existing_message_id=message_id)
        print(f"Пользователь {chat_id} начал процесс обратной связи. Ожидается имя.")


def start_new_order_process(chat_id, user_id, user_name, bot_obj, message_id_to_use, is_preorder=False):
    data_manager.init_user_order_session(chat_id)
    new_order_id = data_manager.create_new_order(chat_id, user_name)
    if is_preorder: data_manager.update_order(new_order_id, {'is_off_hours_order': True, 'status': 'off_hours_pending'})
    data_manager.update_user_session_data(chat_id, 'current_order_id', new_order_id)
    text = "Выберите категорию:"
    if is_preorder: text = "Вы оформляете предзаказ.\n" + text
    user_session = data_manager.get_user_session_data(chat_id);
    cart = user_session.get('cart', [])
    markup = keyboards.categories_keyboard(cart)
    _send_or_edit_main_message(bot_obj, chat_id, text, reply_markup=markup, existing_message_id=message_id_to_use)


def handle_category_selection(call, bot_obj):
    chat_id = call.message.chat.id;
    user_session = data_manager.get_user_session_data(chat_id)
    message_id = user_session.get('main_message_id', call.message.message_id);
    cart = user_session.get('cart', [])
    try:
        bot_obj.answer_callback_query(call.id)
    except Exception as e_ans:
        print(f"Ошибка ответа на callback_query (category_selection {call.data}): {e_ans}")
    if call.data == "menu_unavailable": _send_or_edit_main_message(bot_obj, chat_id, "Меню сейчас обновляется.",
                                                                   reply_markup=keyboards.back_to_main_menu_keyboard(),
                                                                   existing_message_id=message_id); return
    category_name = call.data.split('cat_', 1)[1];
    items_in_category = data_manager.menu_data.get(category_name, [])
    if not items_in_category:
        text = f"В категории '{utils.escape_markdown(category_name)}' пока нет блюд."
        markup = keyboards.categories_keyboard(cart);
        _send_or_edit_main_message(bot_obj, chat_id, text, reply_markup=markup, existing_message_id=message_id);
        return
    markup = keyboards.items_keyboard(category_name, items_in_category, cart)
    text = f"Вы выбрали категорию: *{utils.escape_markdown(category_name)}*\nВыберите блюдо:"
    _send_or_edit_main_message(bot_obj, chat_id, text, reply_markup=markup, existing_message_id=message_id)


# ... (Остальные функции: handle_item_selection, handle_cart_action, и т.д. остаются такими же, как в вашем файле от 01 июня 2025 г., 15:16)
# Убедитесь, что они у вас есть.
def handle_item_selection(call, bot_obj):
    chat_id = call.message.chat.id;
    user_session = data_manager.get_user_session_data(chat_id)
    message_id = user_session.get('main_message_id', call.message.message_id);
    item_id_to_add = call.data.split('item_', 1)[1]
    cart = user_session.get('cart', []);
    selected_item_info = None;
    category_of_selected_item = None
    for category, items_list in data_manager.menu_data.items():
        for item_loop in items_list:
            if item_loop.get(
                'id') == item_id_to_add: selected_item_info = item_loop; category_of_selected_item = category; break
        if selected_item_info: break
    if not selected_item_info:
        try:
            bot_obj.answer_callback_query(call.id, "Товар не найден!", show_alert=True)
        except Exception as e_ans:
            print(f"Ошибка ответа на callback_query (item not found): {e_ans}")
        _send_or_edit_main_message(bot_obj, chat_id, "Произошла ошибка.",
                                   reply_markup=keyboards.categories_keyboard(cart), existing_message_id=message_id);
        return
    item_name_for_cart = selected_item_info.get('name_ru', selected_item_info.get('name_en', 'Неизвестный товар'))
    item_price_for_cart = selected_item_info.get('price', 0);
    item_id_for_cart = selected_item_info.get('id')
    item_in_cart_index = -1
    for i, cart_item_loop in enumerate(cart):
        if cart_item_loop.get('id') == item_id_for_cart: item_in_cart_index = i; break
    if item_in_cart_index != -1:
        cart[item_in_cart_index]['quantity'] += 1
    else:
        cart.append({'id': item_id_for_cart, 'name': item_name_for_cart, 'price': item_price_for_cart, 'quantity': 1})
    data_manager.update_user_session_data(chat_id, 'cart', cart)
    try:
        bot_obj.answer_callback_query(call.id, f"'{item_name_for_cart}' добавлен(а) в корзину!")
    except Exception as e_ans:
        print(f"Ошибка ответа на callback_query (item added): {e_ans}")
    items_in_current_category = data_manager.menu_data.get(category_of_selected_item, [])
    markup = keyboards.items_keyboard(category_of_selected_item, items_in_current_category, cart)
    text = f"Добавлено: {utils.escape_markdown(item_name_for_cart)}.\nКатегория: *{utils.escape_markdown(category_of_selected_item)}*\nВыберите еще или посмотрите корзину:"
    _send_or_edit_main_message(bot_obj, chat_id, text, reply_markup=markup, existing_message_id=message_id)


def handle_cart_action(call, bot_obj):
    chat_id = call.message.chat.id;
    user_session = data_manager.get_user_session_data(chat_id)
    message_id = user_session.get('main_message_id', call.message.message_id);
    action = call.data
    cart = user_session.get('cart', []);
    viewed_removed = user_session.get('viewed_removed_items', [])
    try:
        bot_obj.answer_callback_query(call.id)
    except Exception as e_ans:
        print(f"Ошибка ответа на callback_query (cart_action {action}): {e_ans}")
    item_id_to_remove_from_cart = None
    if action.startswith("cart_remove_"): item_id_to_remove_from_cart = action.split("cart_remove_", 1)[1]
    if action == "cart_show":
        pass
    elif item_id_to_remove_from_cart:
        item_removed_name = None;
        new_cart = []
        for item_in_cart_loop in cart:
            if item_in_cart_loop.get('id') == item_id_to_remove_from_cart:
                item_removed_name = item_in_cart_loop.get('name', 'Неизвестный товар')
                if item_in_cart_loop.get('quantity', 0) > 1: item_in_cart_loop['quantity'] -= 1; new_cart.append(
                    item_in_cart_loop)
            else:
                new_cart.append(item_in_cart_loop)
        if item_removed_name and item_removed_name not in viewed_removed: viewed_removed.append(item_removed_name)
        cart = new_cart;
        data_manager.update_user_session_data(chat_id, 'cart', cart);
        data_manager.update_user_session_data(chat_id, 'viewed_removed_items', viewed_removed)
    elif action == "cart_clear":
        for item_in_cart_loop in cart:
            item_name = item_in_cart_loop.get('name', 'Неизвестный товар')
            if item_name not in viewed_removed: viewed_removed.append(item_name)
        cart = [];
        data_manager.update_user_session_data(chat_id, 'cart', cart);
        data_manager.update_user_session_data(chat_id, 'viewed_removed_items', viewed_removed)
    cart_text = utils.format_cart_text(cart);
    markup = keyboards.cart_keyboard(cart)
    _send_or_edit_main_message(bot_obj, chat_id, cart_text, reply_markup=markup, existing_message_id=message_id)


def handle_order_confirmation_flow(call, bot_obj):
    chat_id = call.message.chat.id;
    user_session = data_manager.get_user_session_data(chat_id)
    message_id = user_session.get('main_message_id', call.message.message_id);
    cart = user_session.get('cart', []);
    order_id = user_session.get('current_order_id')
    try:
        bot_obj.answer_callback_query(call.id)
    except Exception as e_ans:
        print(f"Ошибка ответа на callback_query (order_confirm {call.data}): {e_ans}")
    if call.data == "order_confirm_prompt":
        if not cart: _send_or_edit_main_message(bot_obj, chat_id, "Ваша корзина пуста.",
                                                reply_markup=keyboards.categories_keyboard(cart),
                                                existing_message_id=message_id); return
        cart_summary = utils.format_cart_text(cart);
        text = f"{cart_summary}\n\nПодтвердить заказ и перейти к вводу данных для доставки?"
        markup = keyboards.confirm_action_keyboard("order_confirm_yes", "order_confirm_no", "✅ Да, подтвердить",
                                                   "⬅️ Нет, в корзину")
        _send_or_edit_main_message(bot_obj, chat_id, text, reply_markup=markup, existing_message_id=message_id)
    elif call.data == "order_confirm_yes":
        if not cart: _send_or_edit_main_message(bot_obj, chat_id, "Ваша корзина пуста.",
                                                reply_markup=keyboards.categories_keyboard(cart),
                                                existing_message_id=message_id); return
        if not order_id: _send_or_edit_main_message(bot_obj, chat_id, "Ошибка ID заказа.",
                                                    reply_markup=keyboards.main_menu_keyboard(),
                                                    existing_message_id=message_id); data_manager.clear_user_order_session(
            chat_id); return
        total_price = sum(item.get('price', 0) * item.get('quantity', 0) for item in cart)
        items_for_order = [
            {'id': ci.get('id'), 'name': ci.get('name'), 'price': ci.get('price'), 'quantity': ci.get('quantity')} for
            ci in cart]
        data_manager.update_order(order_id, {'items': items_for_order, 'total_price': total_price,
                                             'original_total_price': total_price, 'status': 'client_confirmed',
                                             'viewed_removed_items_final': list(
                                                 user_session.get('viewed_removed_items', []))})
        data_manager.update_user_session_data(chat_id, 'state', 'awaiting_address')
        _send_or_edit_main_message(bot_obj, chat_id, TEXTS.get('order_take_address', "Укажите адрес доставки:"),
                                   reply_markup=None, existing_message_id=message_id, new_message_if_edit_fails=True)
    elif call.data == "order_confirm_no":
        cart_text = utils.format_cart_text(cart);
        markup = keyboards.cart_keyboard(cart)
        _send_or_edit_main_message(bot_obj, chat_id, cart_text, reply_markup=markup, existing_message_id=message_id)


def process_address_input(message, bot_obj):
    chat_id = message.chat.id;
    user_session = data_manager.get_user_session_data(chat_id)
    main_message_id = user_session.get('main_message_id');
    order_id = user_session.get('current_order_id');
    address = message.text.strip()
    if not order_id or not data_manager.get_order(order_id):
        bot_obj.send_message(chat_id, "Произошла ошибка. Начните сначала.",
                             reply_markup=keyboards.main_menu_keyboard());
        data_manager.clear_user_order_session(chat_id);
        data_manager.update_user_session_data(chat_id, 'state', None);
        return
    data_manager.update_order(order_id, {'address': address, 'status': 'address_received'})
    data_manager.update_user_session_data(chat_id, 'state', 'awaiting_phone')
    if main_message_id:
        try:
            bot_obj.delete_message(chat_id, main_message_id); data_manager.update_user_session_data(chat_id,
                                                                                                    'main_message_id',
                                                                                                    None)
        except Exception as e:
            print(f"Error deleting main_message_id {main_message_id} in process_address_input: {e}")
    try:
        bot_obj.delete_message(chat_id, message.message_id)
    except Exception as e:
        print(f"Error deleting user address message {message.message_id}: {e}")
    new_main_msg = bot_obj.send_message(chat_id, TEXTS.get('order_take_phone', "Укажите номер телефона:"))
    data_manager.update_user_session_data(chat_id, 'main_message_id', new_main_msg.message_id)


def process_phone_input(message, bot_obj):
    chat_id = message.chat.id;
    user_session = data_manager.get_user_session_data(chat_id)
    main_message_id = user_session.get('main_message_id');
    order_id = user_session.get('current_order_id')
    phone_raw = message.text.strip();
    user_id = message.from_user.id;
    user_name = message.from_user.first_name or "Гость"
    if not order_id or not data_manager.get_order(order_id):
        bot_obj.send_message(chat_id, "Произошла ошибка. Начните сначала.",
                             reply_markup=keyboards.main_menu_keyboard());
        data_manager.clear_user_order_session(chat_id);
        data_manager.update_user_session_data(chat_id, 'state', None);
        return
    validated_phone = utils.validate_phone_number(phone_raw)
    if not validated_phone:
        msg_to_send = TEXTS.get('phone_invalid', "Неверный формат телефона.") + "\n" + TEXTS.get('order_take_phone',
                                                                                                 "Укажите номер телефона:")
        _send_or_edit_main_message(bot_obj, chat_id, msg_to_send, existing_message_id=main_message_id,
                                   new_message_if_edit_fails=False)
        try:
            bot_obj.delete_message(chat_id, message.message_id)
        except Exception as e:
            print(f"Error deleting user invalid phone message {message.message_id}: {e}")
        return
    data_manager.update_order(order_id, {'phone': validated_phone, 'status': 'phone_received'})
    try:
        gsheet_manager.find_or_create_client(user_id, user_name, validated_phone)
    except Exception as e:
        print(f"Ошибка gsheet_manager.find_or_create_client (phone): {e}")
    data_manager.update_user_session_data(chat_id, 'state', 'awaiting_client_comment_prompt')
    if main_message_id:
        try:
            bot_obj.delete_message(chat_id, main_message_id); data_manager.update_user_session_data(chat_id,
                                                                                                    'main_message_id',
                                                                                                    None)
        except Exception as e:
            print(f"Error deleting main_message_id {main_message_id} in process_phone_input: {e}")
    try:
        bot_obj.delete_message(chat_id, message.message_id)
    except Exception as e:
        print(f"Error deleting user phone message {message.message_id}: {e}")
    order_data = data_manager.get_order(order_id);
    summary = utils.format_order_details_for_client(order_data)
    text = f"Спасибо! Ваш заказ `№{order_id}` почти оформлен.\n{summary}\n\nХотите оставить комментарий к заказу?"
    markup = keyboards.confirm_action_keyboard(f"client_comment_yes_{order_id}", f"client_comment_no_{order_id}", "Да",
                                               "Нет")
    new_main_msg = bot_obj.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    data_manager.update_user_session_data(chat_id, 'main_message_id', new_main_msg.message_id)


def handle_client_comment_prompt(call, bot_obj):
    chat_id = call.message.chat.id;
    user_session = data_manager.get_user_session_data(chat_id)
    message_id = user_session.get('main_message_id', call.message.message_id);
    order_id = call.data.split('_')[-1]
    try:
        bot_obj.answer_callback_query(call.id)
    except Exception as e_ans:
        print(f"Ошибка ответа на callback_query (comment_prompt {call.data}): {e_ans}")
    if user_session.get('current_order_id') != order_id:
        _send_or_edit_main_message(bot_obj, chat_id, "Произошла ошибка. Начните заново.",
                                   reply_markup=keyboards.main_menu_keyboard(), existing_message_id=message_id);
        data_manager.clear_user_order_session(chat_id);
        return
    if call.data.startswith("client_comment_yes_"):
        data_manager.update_user_session_data(chat_id, 'state', 'awaiting_client_comment')
        _send_or_edit_main_message(bot_obj, chat_id, "Пожалуйста, введите ваш комментарий к заказу:", reply_markup=None,
                                   existing_message_id=message_id)
    elif call.data.startswith("client_comment_no_"):
        finalize_client_order_submission(chat_id, order_id, bot_obj, message_id_to_edit=message_id)


def process_client_comment(message, bot_obj):
    chat_id = message.chat.id;
    user_session = data_manager.get_user_session_data(chat_id)
    main_message_id = user_session.get('main_message_id');
    order_id = user_session.get('current_order_id');
    comment = message.text.strip()
    if not order_id or not data_manager.get_order(order_id):
        bot_obj.send_message(chat_id, "Произошла ошибка. Начните сначала.",
                             reply_markup=keyboards.main_menu_keyboard());
        data_manager.clear_user_order_session(chat_id);
        data_manager.update_user_session_data(chat_id, 'state', None);
        return
    data_manager.update_order(order_id,
                              {'client_comment': comment, 'last_updated_utc': datetime.utcnow().isoformat() + "Z"})
    if main_message_id:
        try:
            bot_obj.delete_message(chat_id, main_message_id); data_manager.update_user_session_data(chat_id,
                                                                                                    'main_message_id',
                                                                                                    None)
        except Exception as e:
            print(f"Error deleting main_message_id {main_message_id} in process_client_comment: {e}")
    try:
        bot_obj.delete_message(chat_id, message.message_id)
    except Exception as e:
        print(f"Error deleting user comment message {message.message_id}: {e}")
    finalize_client_order_submission(chat_id, order_id, bot_obj)


def finalize_client_order_submission(chat_id, order_id, bot_obj, message_id_to_edit=None):
    user_id = chat_id;
    order_data = data_manager.get_order(order_id)
    if not order_data: return
    final_status = 'processing';
    now_utc_iso = datetime.utcnow().isoformat() + "Z"
    if order_data.get('is_off_hours_order'): final_status = 'off_hours_pending'
    data_manager.update_order(order_id, {'status': final_status, 'finalized_at_utc': now_utc_iso,
                                         'last_updated_utc': now_utc_iso})
    order_data = data_manager.get_order(order_id)
    client_summary = utils.format_order_details_for_client(order_data)
    final_text = f"✅ Спасибо! Ваш заказ `№{order_id}` принят.\n\n{client_summary}"
    if order_data.get('is_off_hours_order'): final_text += "\n\nНапоминаем, это предзаказ."
    final_text += "\n\nОжидайте информации по оплате от администратора."
    if message_id_to_edit:
        edited_msg = _send_or_edit_main_message(bot_obj, chat_id, final_text,
                                                reply_markup=keyboards.back_to_main_menu_keyboard(),
                                                existing_message_id=message_id_to_edit, parse_mode='Markdown',
                                                new_message_if_edit_fails=False)
        if not edited_msg: new_main_msg = bot_obj.send_message(chat_id, final_text,
                                                               reply_markup=keyboards.back_to_main_menu_keyboard(),
                                                               parse_mode='Markdown'); data_manager.update_user_session_data(
            chat_id, 'main_message_id', new_main_msg.message_id)
    else:
        new_main_msg = bot_obj.send_message(chat_id, final_text, reply_markup=keyboards.back_to_main_menu_keyboard(),
                                            parse_mode='Markdown'); data_manager.update_user_session_data(chat_id,
                                                                                                          'main_message_id',
                                                                                                          new_main_msg.message_id)
    admin_summary = utils.format_order_details_for_admin(order_data)
    admin_markup = keyboards.admin_order_keyboard(order_id, order_data.get('status', 'N/A'))
    try:
        if ADMIN_GROUP_ID:
            admin_msg = bot_obj.send_message(ADMIN_GROUP_ID, admin_summary, reply_markup=admin_markup,
                                             parse_mode='Markdown')
            data_manager.update_order(order_id, {'admin_group_message_id': admin_msg.message_id})
    except Exception as e:
        print(f"Ошибка отправки заказа {order_id} в группу {ADMIN_GROUP_ID}: {e}")
    try:
        gsheet_manager.update_client_order_info(user_id, order_data.get('total_price', 0))
    except Exception as e:
        print(f"Ошибка gsheet_manager.update_client_order_info: {e}")
    data_manager.update_user_session_data(chat_id, 'cart', []);
    data_manager.update_user_session_data(chat_id, 'viewed_removed_items', [])


def handle_client_confirm_delivery(call, bot_obj):
    chat_id = call.message.chat.id;
    try:
        order_id = call.data.split('client_delivery_confirmed_')[1]
    except IndexError:
        print(f"Ошибка извлечения order_id: {call.data}"); return
    user_session = data_manager.get_user_session_data(chat_id);
    main_message_id_for_client = user_session.get('main_message_id', call.message.message_id)
    try:
        bot_obj.answer_callback_query(call.id, TEXTS.get("order_received_notification", "Заказ получен! Спасибо!"))
    except Exception as e_ans:
        print(f"Ошибка ответа на callback_query (client_confirm_delivery): {e_ans}")
    now_utc_iso = datetime.utcnow().isoformat() + "Z"
    if data_manager.update_order(order_id, {'status': 'client_confirmed_delivery',
                                            'client_confirmed_delivery_at_utc': now_utc_iso,
                                            'completed_at_utc': now_utc_iso, 'last_updated_utc': now_utc_iso}):
        if 'admin_handlers' in globals() and hasattr(admin_handlers, '_update_admin_order_message'):
            admin_handlers._update_admin_order_message(bot_obj, order_id,
                                                       f"Client confirmed delivery for order #{order_id}.")
        client_order_data = data_manager.get_order(order_id);
        updated_client_text = utils.format_order_details_for_client(client_order_data)
        review_request_text = TEXTS.get('order_delivery_confirmed_ask_review',
                                        'Спасибо за подтверждение! Оставьте, пожалуйста, отзыв.')
        updated_client_text += f"\n\n{review_request_text}"
        _send_or_edit_main_message(bot_obj, chat_id, updated_client_text,
                                   reply_markup=keyboards.back_to_main_menu_keyboard(),
                                   existing_message_id=main_message_id_for_client)
        data_manager.update_user_session_data(chat_id, 'state', f'awaiting_review_text_{order_id}')
        data_manager.update_user_session_data(chat_id, 'current_order_id', order_id)
        print(f"Запрошен отзыв у клиента {chat_id} по заказу {order_id} после подтверждения доставки.")
    else:
        print(f"Не удалось обновить статус заказа {order_id} на client_confirmed_delivery.")


def handle_navigation_callbacks(call, bot_obj):
    chat_id = call.message.chat.id;
    user_session = data_manager.get_user_session_data(chat_id)
    message_id = user_session.get('main_message_id', call.message.message_id)
    user_name = call.from_user.first_name or "Гость";
    user_id = call.from_user.id
    try:
        bot_obj.answer_callback_query(call.id)
    except Exception as e_ans:
        print(f"Ошибка ответа на callback_query (navigation {call.data}): {e_ans}")

    current_state = user_session.get('state', "")  # ИСПРАВЛЕНО ЗДЕСЬ

    if call.data == "to_main_menu":
        # Не сбрасываем сессию, если ожидается отзыв ИЛИ ожидается ввод данных для обратной связи
        if not (current_state.startswith('awaiting_review_text_') or \
                current_state.startswith('awaiting_feedback_')) and \
                (user_session.get('current_order_id') or user_session.get('feedback_info') or current_state != ""):
            print(f"Пользователь {chat_id} ушел в главное меню, сбрасываем активную сессию.")
            data_manager.clear_user_order_session(
                chat_id)  # Эта функция теперь должна просто сбрасывать state и cart/current_order_id
            data_manager.update_user_session_data(chat_id, 'feedback_info', {})  # Отдельно очищаем feedback_info
            data_manager.update_user_session_data(chat_id, 'state', None)  # Явный сброс состояния

        text = f"Главное меню, {utils.escape_markdown(user_name)}."
        markup = keyboards.main_menu_keyboard()
        _send_or_edit_main_message(bot_obj, chat_id, text, reply_markup=markup, existing_message_id=message_id,
                                   photo_path=WELCOME_IMAGE_PATH)

    elif call.data == "to_categories":
        text = "Выберите категорию:";
        cart = user_session.get('cart', [])
        markup = keyboards.categories_keyboard(cart)
        _send_or_edit_main_message(bot_obj, chat_id, text, reply_markup=markup, existing_message_id=message_id)
    elif call.data == "preorder_yes":
        start_new_order_process(chat_id, user_id, user_name, bot_obj, message_id, is_preorder=True)
    elif call.data == "preorder_no":
        _send_or_edit_main_message(bot_obj, chat_id, "Хорошо. Вы всегда можете вернуться позже!",
                                   reply_markup=keyboards.main_menu_keyboard(), existing_message_id=message_id)


# --- НОВЫЕ ФУНКЦИИ ДЛЯ ОБРАТНОЙ СВЯЗИ ---
def process_feedback_name(message, bot_obj):
    chat_id = message.chat.id
    user_name_for_feedback = message.text.strip()
    user_session = data_manager.get_user_session_data(chat_id)
    main_message_id = user_session.get('main_message_id')

    if not user_name_for_feedback:
        bot_obj.send_message(chat_id, "Имя не может быть пустым. Пожалуйста, введите ваше имя:")
        return

    feedback_info = user_session.get('feedback_info', {})
    feedback_info['name'] = user_name_for_feedback
    data_manager.update_user_session_data(chat_id, 'feedback_info', feedback_info)
    data_manager.update_user_session_data(chat_id, 'state', 'awaiting_feedback_phone')

    prompt_text = TEXTS.get("feedback_prompt_phone", "Пожалуйста, введите ваш контактный телефон:")

    try:
        bot_obj.delete_message(chat_id, message.message_id)
    except Exception as e:
        print(f"Error deleting user feedback name message: {e}")

    _send_or_edit_main_message(bot_obj, chat_id, prompt_text,
                               reply_markup=keyboards.back_to_main_menu_keyboard(),
                               existing_message_id=main_message_id,
                               new_message_if_edit_fails=True)
    print(f"Пользователь {chat_id} ввел имя для обратной связи: '{user_name_for_feedback}'. Ожидается телефон.")


def process_feedback_phone(message, bot_obj):
    chat_id = message.chat.id
    phone_for_feedback = message.text.strip()
    user_session = data_manager.get_user_session_data(chat_id)
    main_message_id = user_session.get('main_message_id')
    feedback_info = user_session.get('feedback_info', {})

    if not phone_for_feedback:
        bot_obj.send_message(chat_id,
                             "Номер телефона не может быть пустым. Пожалуйста, введите ваш контактный телефон:")
        return

    feedback_info['phone'] = phone_for_feedback
    data_manager.update_user_session_data(chat_id, 'feedback_info', feedback_info)
    data_manager.update_user_session_data(chat_id, 'state', 'awaiting_feedback_message')

    prompt_text = TEXTS.get("feedback_prompt_message", "Напишите ваше сообщение/отзыв/предложение:")

    try:
        bot_obj.delete_message(chat_id, message.message_id)
    except Exception as e:
        print(f"Error deleting user feedback phone message: {e}")

    _send_or_edit_main_message(bot_obj, chat_id, prompt_text,
                               reply_markup=keyboards.back_to_main_menu_keyboard(),
                               existing_message_id=main_message_id,
                               new_message_if_edit_fails=True)
    print(f"Пользователь {chat_id} ввел телефон для обратной связи: '{phone_for_feedback}'. Ожидается сообщение.")


def process_feedback_message(message, bot_obj):
    chat_id = message.chat.id
    feedback_text = message.text.strip()
    user_session = data_manager.get_user_session_data(chat_id)
    main_message_id = user_session.get('main_message_id')
    feedback_info = user_session.get('feedback_info', {})

    if not feedback_text:
        bot_obj.send_message(chat_id,
                             "Сообщение обратной связи не может быть пустым. Пожалуйста, напишите ваше сообщение:")
        return

    feedback_info['message'] = feedback_text
    telegram_user_name = message.from_user.first_name
    if message.from_user.last_name: telegram_user_name += f" {message.from_user.last_name}"
    if message.from_user.username: telegram_user_name += f" (@{message.from_user.username})"
    telegram_user_id = message.from_user.id

    admin_notification_template = TEXTS.get("feedback_admin_notification_format",
                                            ("Feedback Received:\n"
                                             "Telegram User: {telegram_user_name} (ID: `{telegram_user_id}`)\n"
                                             "Provided Name: {feedback_name}\n"
                                             "Provided Phone: {feedback_phone}\n\n"
                                             "Message:\n{feedback_message}"))
    admin_message_text = admin_notification_template.format(
        telegram_user_name=utils.escape_markdown(telegram_user_name),
        telegram_user_id=telegram_user_id,
        feedback_name=utils.escape_markdown(feedback_info.get('name', '-')),
        feedback_phone=utils.escape_markdown(feedback_info.get('phone', '-')),
        feedback_message=utils.escape_markdown(feedback_text)
    )
    if ADMIN_GROUP_ID:
        try:
            bot_obj.send_message(ADMIN_GROUP_ID, admin_message_text, parse_mode='Markdown')
        except Exception as e:
            print(f"Ошибка отправки обратной связи в группу администраторов: {e}")
    else:
        print("ADMIN_GROUP_ID не настроен. Обратная связь не отправлена администраторам.")
    thanks_text = TEXTS.get("feedback_thanks", "Спасибо за вашу обратную связь! Мы ее изучим.")
    try:
        bot_obj.delete_message(chat_id, message.message_id)
    except Exception as e:
        print(f"Error deleting user feedback text message: {e}")

    # После отправки благодарности, возвращаем в главное меню
    send_welcome(message, bot_obj)  # ИЗМЕНЕНИЕ: Вызываем send_welcome для возврата в главное меню

    # Очищаем состояние и данные обратной связи (теперь это делает init_user_order_session в send_welcome)
    # data_manager.update_user_session_data(chat_id, 'state', None)
    # data_manager.update_user_session_data(chat_id, 'feedback_info', {})
    print(f"Пользователь {chat_id} завершил процесс обратной связи.")


print("Модуль client_handlers.py загружен.")