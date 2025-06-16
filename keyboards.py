# keyboards.py
from telebot import types
import data_manager


def main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_make_order = types.InlineKeyboardButton(text="📖 Сделать заказ", callback_data="main_make_order")
    btn_cafe_status = types.InlineKeyboardButton(text="🕒 Время работы", callback_data="main_cafe_status")
    btn_feedback = types.InlineKeyboardButton(text="✍️ Обратная связь", callback_data="main_feedback")
    markup.add(btn_make_order, btn_cafe_status, btn_feedback)
    return markup


def categories_keyboard(cart_items_for_check=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    categories = data_manager.menu_data.keys()
    buttons = []
    if not categories:
        buttons.append(types.InlineKeyboardButton(text="Меню временно недоступно", callback_data="menu_unavailable"))
    else:
        for category_name in categories:
            buttons.append(types.InlineKeyboardButton(text=category_name, callback_data=f"cat_{category_name}"))
    markup.add(*buttons)

    cart_button_text = "🛒 Показать корзину"
    if cart_items_for_check:
        total_quantity = sum(cart_item.get('quantity', 0) for cart_item in cart_items_for_check)
        if total_quantity > 0:
            cart_button_text = f"✅ 🛒 Показать корзину ({total_quantity} шт.)"
    markup.row(types.InlineKeyboardButton(text=cart_button_text, callback_data="cart_show"))

    # ИЗМЕНЕНИЕ: Кнопка "В главное меню" УДАЛЕНА отсюда
    # markup.row(types.InlineKeyboardButton(text="⬅️ В главное меню", callback_data="to_main_menu"))
    return markup


def items_keyboard(category_name, items, cart_items_for_checkmark=None):
    if cart_items_for_checkmark is None: cart_items_for_checkmark = []
    cart_item_ids = {cart_item['id'] for cart_item in cart_items_for_checkmark}
    markup = types.InlineKeyboardMarkup(row_width=1)
    if not items:
        markup.add(
            types.InlineKeyboardButton(text="В этой категории пока нет товаров", callback_data=f"cat_{category_name}"))
    else:
        for item in items:
            display_name = item.get('name_ru', item.get('name_en', 'Название не найдено'))
            price = item.get('price', 0)
            item_text = f"{display_name} - {price / 1000:.0f}K"
            item_id = item.get('id', 'unknown_item_id_missing')
            if item_id in cart_item_ids: item_text = f"✅ {item_text}"
            markup.add(types.InlineKeyboardButton(text=item_text, callback_data=f"item_{item_id}"))

    cart_button_text = "🛒 Показать корзину"
    if cart_items_for_checkmark:
        total_quantity = sum(cart_item.get('quantity', 0) for cart_item in cart_items_for_checkmark)
        if total_quantity > 0: cart_button_text = f"✅ 🛒 Показать корзину ({total_quantity} шт.)"
    markup.row(types.InlineKeyboardButton(text=cart_button_text, callback_data="cart_show"))
    markup.row(types.InlineKeyboardButton(text="⬅️ К категориям", callback_data="to_categories"))  # Эта кнопка остается
    return markup


def cart_keyboard(cart_items):
    markup = types.InlineKeyboardMarkup(row_width=1)
    if not cart_items:
        markup.add(types.InlineKeyboardButton(text="Корзина пуста. К выбору блюд 🍽️", callback_data="to_categories"))
    else:
        for item in cart_items:
            item_name_in_cart = item.get('name', 'Товар');
            quantity_in_cart = item.get('quantity', 0)
            price_in_cart = item.get('price', 0);
            item_id_in_cart = item.get('id', 'unknown_cart_item_id')
            item_text = f"❌ {item_name_in_cart} ({quantity_in_cart} шт.) - {price_in_cart * quantity_in_cart / 1000:.0f}K"
            markup.add(types.InlineKeyboardButton(text=item_text, callback_data=f"cart_remove_{item_id_in_cart}"))
        markup.row(types.InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="order_confirm_prompt"))
        markup.row(types.InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="cart_clear"))
        markup.row(types.InlineKeyboardButton(text="⬅️ Продолжить выбор", callback_data="to_categories"))
    markup.row(types.InlineKeyboardButton(text="⬅️ В главное меню", callback_data="to_main_menu"))  # Здесь она нужна
    return markup


def confirm_action_keyboard(yes_callback, no_callback, yes_text="Да", no_text="Нет", lang="ru"):
    if lang == "en":
        yes_text = "✅ Yes, Confirm"
        no_text = "❌ No, Cancel"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton(text=yes_text, callback_data=yes_callback),
               types.InlineKeyboardButton(text=no_text, callback_data=no_callback))
    return markup


def back_to_main_menu_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="⬅️ В главное меню", callback_data="to_main_menu"))
    return markup


def client_confirm_delivery_keyboard(order_id):
    text = "📦 Я получил(а) заказ"
    callback = f"client_delivery_confirmed_{order_id}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text=text, callback_data=callback))
    return markup


def admin_order_keyboard(order_id, current_status):  # Без изменений
    markup = types.InlineKeyboardMarkup(row_width=2)
    if current_status in ['processing', 'off_hours_pending', 'payment_rejected'] and \
            current_status not in ['awaiting_payment', 'payment_verification', 'payment_received',
                                   'delivering', 'completed', 'cancelled_by_admin', 'cancelled_by_client',
                                   'client_confirmed_delivery']:
        markup.add(types.InlineKeyboardButton(text="💰 Request Payment", callback_data=f"admin_req_payment_{order_id}"))
    if current_status == 'payment_verification':
        markup.add(
            types.InlineKeyboardButton(text="👍 Receipt OK (Paid)", callback_data=f"admin_payment_recv_{order_id}"))
        markup.add(types.InlineKeyboardButton(text="👎 Receipt Problem (Reject)",
                                              callback_data=f"admin_payment_reject_{order_id}"))
        markup.add(types.InlineKeyboardButton(text="💬 Comment to Client (re:receipt)",
                                              callback_data=f"admin_comment_client_{order_id}"))
    elif current_status not in ['completed', 'cancelled_by_admin', 'cancelled_by_client', 'client_confirmed_delivery']:
        if current_status in ['pending_client_info', 'client_confirmed', 'address_received',
                              'phone_received', 'off_hours_pending', 'processing',
                              'awaiting_payment', 'payment_rejected']:
            markup.add(types.InlineKeyboardButton(text="💲 Adjust Sum", callback_data=f"admin_adj_sum_{order_id}"))
        markup.add(
            types.InlineKeyboardButton(text="💬 Comment to Client", callback_data=f"admin_comment_client_{order_id}"))
        if current_status not in ['payment_verification', 'payment_received', 'delivering']:
            markup.add(types.InlineKeyboardButton(text="✅ Mark as Paid (manual)",
                                                  callback_data=f"admin_payment_recv_{order_id}"))
        if current_status not in ['delivering']:
            markup.add(types.InlineKeyboardButton(text="🛵 Delivering", callback_data=f"admin_delivering_{order_id}"))
        if current_status != 'client_confirmed_delivery':
            markup.add(types.InlineKeyboardButton(text="🏁 Mark Completed", callback_data=f"admin_completed_{order_id}"))
        markup.add(types.InlineKeyboardButton(text="❌ Cancel Order", callback_data=f"admin_cancel_order_{order_id}"))
    else:
        status_display = current_status
        if current_status == 'client_confirmed_delivery':
            status_display = "Completed (Client Confirmed Delivery)"
        elif current_status == 'completed':
            status_display = "Completed (Admin)"
        markup.add(types.InlineKeyboardButton(text=f"Status: {status_display}", callback_data=f"admin_noop_{order_id}"))
    markup.row(types.InlineKeyboardButton(text="🔄 Refresh Info", callback_data=f"admin_refresh_order_{order_id}"))
    return markup


def admin_cafe_status_keyboard():  # Без изменений
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🟢 Open Cafe (Manual)", callback_data="admin_cafe_manual_open"))
    markup.add(types.InlineKeyboardButton("🔴 Close Cafe (Manual)", callback_data="admin_cafe_manual_close"))
    markup.add(types.InlineKeyboardButton("⚙️ Auto Schedule Mode", callback_data="admin_cafe_auto"))
    return markup


print("Модуль keyboards загружен.")