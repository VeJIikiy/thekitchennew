# utils.py
import re
from datetime import datetime, time as dt_time, timedelta
import pytz
from config import CAFE_SCHEDULE, DEFAULT_TIMEZONE, TEXTS
import data_manager

def escape_markdown(text):
    if not isinstance(text, str): text = str(text)
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return "".join(['\\' + char if char in escape_chars else char for char in text])

def get_cafe_operational_status_details():
    manual_status_info = data_manager.get_cafe_status(); override_status = manual_status_info.get('status', 'auto')
    manual_message = manual_status_info.get('manual_message'); schedule_text_parts = ["\n📋 *Наше расписание:*"]
    day_names_map = {'weekdays': "Будни", 0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 'saturday': "Сб", 5: "Сб", 'sunday': "Вс", 6: "Вс"}
    ordered_keys_for_display = [];
    if 'weekdays' in CAFE_SCHEDULE: ordered_keys_for_display.append('weekdays')
    for i in range(5):
        if i in CAFE_SCHEDULE and 'weekdays' not in CAFE_SCHEDULE: ordered_keys_for_display.append(i)
    if 'saturday' in CAFE_SCHEDULE: ordered_keys_for_display.append('saturday')
    elif 5 in CAFE_SCHEDULE: ordered_keys_for_display.append(5)
    if 'sunday' in CAFE_SCHEDULE: ordered_keys_for_display.append('sunday')
    elif 6 in CAFE_SCHEDULE: ordered_keys_for_display.append(6)
    final_display_order = []; seen_days_numeric = set()
    for key in ordered_keys_for_display:
        is_group_key = isinstance(key, str)
        if not is_group_key:
            if key in seen_days_numeric: continue
            if 0 <= key <= 4 and 'weekdays' in CAFE_SCHEDULE and 'weekdays' in final_display_order: continue
            if key == 5 and 'saturday' in CAFE_SCHEDULE and 'saturday' in final_display_order: continue
            if key == 6 and 'sunday' in CAFE_SCHEDULE and 'sunday' in final_display_order: continue
        if key not in final_display_order: final_display_order.append(key)
        if key == 'weekdays': seen_days_numeric.update(range(5))
        elif key == 'saturday': seen_days_numeric.add(5)
        elif key == 'sunday': seen_days_numeric.add(6)
        elif not is_group_key: seen_days_numeric.add(key)
    for key in final_display_order:
        hours = CAFE_SCHEDULE.get(key); day_display_name = day_names_map.get(key, str(key))
        if hours == 'closed': schedule_text_parts.append(f"  {escape_markdown(day_display_name)}: Выходной")
        elif isinstance(hours, dict): schedule_text_parts.append(f"  {escape_markdown(day_display_name)}: {hours.get('open','N/A')} - {hours.get('close','N/A')}")
    full_schedule_text = "\n".join(schedule_text_parts); is_open_now = False; status_line = ""
    try: tz = pytz.timezone(DEFAULT_TIMEZONE)
    except pytz.exceptions.UnknownTimeZoneError: tz = pytz.utc; full_schedule_text += f"\nПРЕДУПРЕЖДЕНИЕ: DEFAULT_TIMEZONE!"
    now_local = datetime.now(tz); current_time_str = now_local.strftime("%H:%M"); current_day_of_week = now_local.weekday()
    if override_status == 'manual_open': is_open_now = True; status_line = "✅ Кафе сейчас *ОТКРЫТО* (вручную)."
    elif override_status == 'manual_close': is_open_now = False; status_line = "🔴 Кафе сейчас *ЗАКРЫТО* (вручную)."
    else:
        day_key_for_schedule_check = current_day_of_week
        if current_day_of_week in CAFE_SCHEDULE: day_key_for_schedule_check = current_day_of_week
        elif 0 <= current_day_of_week <= 4 and 'weekdays' in CAFE_SCHEDULE: day_key_for_schedule_check = 'weekdays'
        elif current_day_of_week == 5 and 'saturday' in CAFE_SCHEDULE: day_key_for_schedule_check = 'saturday'
        elif current_day_of_week == 6 and 'sunday' in CAFE_SCHEDULE: day_key_for_schedule_check = 'sunday'
        current_day_schedule_info = CAFE_SCHEDULE.get(day_key_for_schedule_check)
        if not current_day_schedule_info or current_day_schedule_info == 'closed': is_open_now = False; status_line = f"🔴 Кафе сегодня *закрыто*."
        elif isinstance(current_day_schedule_info, dict):
            open_time_str=current_day_schedule_info.get('open','00:00'); close_time_str=current_day_schedule_info.get('close','00:00')
            if open_time_str <= current_time_str < close_time_str: is_open_now = True; status_line = f"✅ Кафе сейчас *ОТКРЫТО* (до {close_time_str})."
            elif current_time_str < open_time_str: is_open_now = False; status_line = f"🔴 Кафе откроется в {open_time_str}."
            else: is_open_now = False; status_line = f"🔴 Кафе сегодня уже закрылось (работало до {close_time_str})."
        else: is_open_now = False; status_line = "🔴 Ошибка в расписании."
    if manual_message and override_status != 'auto' : status_line += f"\nℹ️ Сообщение: _{escape_markdown(manual_message)}_"
    return {'is_open': is_open_now, 'status_line': status_line, 'schedule_text': full_schedule_text}

def validate_phone_number(phone_str):
    if not isinstance(phone_str, str): return None
    cleaned_phone = "".join(filter(lambda char: char.isdigit() or char == '+', phone_str))
    if phone_str.startswith('+') and not cleaned_phone.startswith('+'): return None
    if not phone_str.startswith('+') and cleaned_phone.startswith('+'): return None
    check_digits_part = cleaned_phone[1:] if cleaned_phone.startswith('+') else cleaned_phone
    if not check_digits_part.isdigit(): return None
    if 10 <= len(check_digits_part) <= 15: return cleaned_phone
    return None

def format_cart_text(cart_items):
    if not cart_items: return "🛒 Ваша корзина пуста."
    text = "🛒 *Ваша корзина:*\n\n"; total_cart_price = 0
    for i, item in enumerate(cart_items):
        item_name = item.get('name', 'Неизвестный товар'); item_price = item.get('price', 0); item_quantity = item.get('quantity', 0)
        item_total = item_price * item_quantity
        price_unit_str = f"{item_price / 1000:.0f}K" if item_price % 1000 == 0 and item_price !=0 else str(item_price)
        item_total_str = f"{item_total / 1000:.0f}K" if item_total % 1000 == 0 and item_total !=0 else str(item_total)
        text += f"{i + 1}. {escape_markdown(item_name)} ({item_quantity} шт.) - {item_total_str}\n"; total_cart_price += item_total
    total_cart_price_str = f"{total_cart_price / 1000:.0f}K" if total_cart_price % 1000 == 0 and total_cart_price !=0 else str(total_cart_price)
    text += f"\n*Итого по корзине:* {total_cart_price_str}"; return text

def _format_timestamp_local(timestamp_utc_str, tz_info): # Вспомогательная функция для дат
    if not timestamp_utc_str: return ""
    try:
        dt_utc = datetime.fromisoformat(timestamp_utc_str.replace('Z', '+00:00'))
        dt_local = dt_utc.astimezone(tz_info)
        return dt_local.strftime('%Y-%m-%d %H:%M:%S %Z')
    except Exception: return timestamp_utc_str

def format_order_details_for_client(order_data, include_status=True, include_contact_info=True):
    if not order_data: return "Не удалось найти информацию о заказе."
    try: local_tz = pytz.timezone(DEFAULT_TIMEZONE)
    except pytz.exceptions.UnknownTimeZoneError: local_tz = pytz.utc
    status_translations_ru = {
        'pending_client_info': "⏳ Ожидание данных", 'client_confirmed': "📝 Подтвержден, ждем адрес",
        'address_received': "📍 Адрес получен", 'phone_received': "📱 Телефон получен",
        'off_hours_pending': "⏰ Предзаказ принят", 'processing': "⏳ В обработке",
        'awaiting_payment': "💳 Ожидание оплаты", 'payment_verification': "🧐 Проверка оплаты",
        'payment_rejected': "⚠️ Оплата отклонена", 'payment_received': "✅ Оплата получена!",
        'delivering': "🛵 В доставке", 'client_confirmed_delivery': "📦 Доставку подтвердил(а)",
        'completed': "🏁 Выполнен!", 'cancelled_by_client': "❌ Отменен вами", 'cancelled_by_admin': "❌ Отменен админом"
    }
    order_id_str = escape_markdown(order_data.get('order_id','N/A')); lines = [f"🧾 *Заказ №{order_id_str}*"]
    status_key = order_data.get('status', 'N/A')
    if include_status:
        current_status_text = status_translations_ru.get(status_key, escape_markdown(status_key))
        lines.append(f"Статус: **{current_status_text.upper()}**") # Статус жирным и большим
    created_at_str = _format_timestamp_local(order_data.get('created_at_utc'), local_tz)
    if created_at_str: lines.append(f"Создан: `{created_at_str}`")
    if order_data.get('items'):
        lines.append("\n🛍️ *Состав заказа:*")
        for item in order_data['items']:
            item_name = item.get('name_ru', item.get('name', 'Неизвестный товар'))
            item_price = item.get('price', 0); item_quantity = item.get('quantity', 0); item_total = item_price * item_quantity
            price_unit_str = f"{item_price/1000:.0f}K" if item_price%1000==0 and item_price!=0 else str(item_price)
            item_total_str = f"{item_total/1000:.0f}K" if item_total%1000==0 and item_total!=0 else str(item_total)
            lines.append(f"- {escape_markdown(item_name)} ({item_quantity} шт. x {price_unit_str}) = {item_total_str}")
    else: lines.append("\n🛍️ *Состав заказа:* (пусто)")
    final_price = order_data.get('total_price',0); original_total = order_data.get('original_total_price'); adjustment_amount = order_data.get('adjustment_amount', 0)
    lines.append("")
    if original_total is not None and original_total != final_price and adjustment_amount != 0:
        original_total_str = f"{original_total/1000:.0f}K" if original_total%1000==0 and original_total!=0 else str(original_total)
        lines.append(f"Изначальная сумма: {original_total_str}")
        adj_type = "Скидка" if adjustment_amount < 0 else "Надбавка"; lines.append(f"{adj_type}: {abs(adjustment_amount) / 1000:.0f}K")
        adj_comment = order_data.get('adjustment_comment');
        if adj_comment: lines.append(f"Комментарий к сумме: _{escape_markdown(adj_comment)}_")
    final_price_str = f"{final_price/1000:.0f}K" if final_price%1000==0 and final_price!=0 else str(final_price)
    lines.append(f"💰 *Итого к оплате: {final_price_str}*")
    if include_contact_info:
        if order_data.get('address'): lines.append(f"\n📍 *Адрес доставки:* {escape_markdown(order_data['address'])}")
        if order_data.get('phone'): lines.append(f"📱 *Телефон для связи:* {escape_markdown(order_data['phone'])}")
    if order_data.get('client_comment'): lines.append(f"\n✏️ *Ваш комментарий:* _{escape_markdown(order_data['client_comment'])}_")
    admin_comments_to_client = [ac for ac in order_data.get('admin_comments', []) if ac]
    if admin_comments_to_client:
        lines.append("\n🗣️ *Комментарии от кафе:*")
        for comment in admin_comments_to_client: lines.append(f"- _{escape_markdown(comment)}_")
    if order_data.get('is_off_hours_order') and status_key not in ['completed', 'delivering', 'payment_received', 'cancelled_by_admin', 'cancelled_by_client', 'client_confirmed_delivery']:
        lines.append("\n_(*Это предзаказ, он будет обработан в рабочее время кафе*)_")
    review_text = order_data.get('review_text')
    if review_text: lines.append(f"\n🌟 *Ваш отзыв:* _{escape_markdown(review_text)}_")
    return "\n".join(lines)

def format_order_details_for_admin(order_data):
    if not order_data: return "Order details not found."
    try: local_tz = pytz.timezone(DEFAULT_TIMEZONE)
    except pytz.exceptions.UnknownTimeZoneError: local_tz = pytz.utc
    order_id_str = str(order_data.get('order_id','N/A')); status_key = order_data.get('status','N/A')
    status_translations_en = {
        'pending_client_info': "Pending Client Info", 'client_confirmed': "Client Confirmed", 'address_received': "Address Received",
        'phone_received': "Phone Received", 'off_hours_pending': "Off-hours Pending", 'processing': "Processing",
        'awaiting_payment': "Awaiting Payment", 'payment_verification': "Payment Verification",
        'payment_rejected': "Payment Rejected", 'payment_received': "Payment Received", 'delivering': "Delivering",
        'client_confirmed_delivery': "Client Confirmed Delivery", 'completed': "Completed",
        'cancelled_by_client': "Cancelled by Client", 'cancelled_by_admin': "Cancelled by Admin"
    }
    status_en = status_translations_en.get(status_key, escape_markdown(status_key).upper())
    client_name_str = str(order_data.get('client_name','N/A')); client_chat_id_str = str(order_data.get('client_chat_id'))
    lines = [f"🔔 *Order Details: #{escape_markdown(order_id_str)}*"]; lines.append(f"*Status: `{status_en}`*")
    lines.append(f"Client: {escape_markdown(client_name_str)} (ChatID: `{client_chat_id_str}`)")
    created_at_str = _format_timestamp_local(order_data.get('created_at_utc'), local_tz)
    if created_at_str: lines.append(f"Created: `{created_at_str}`")
    finalized_at_str = _format_timestamp_local(order_data.get('finalized_at_utc'), local_tz)
    if finalized_at_str: lines.append(f"Client Finalized: `{finalized_at_str}`")
    payment_request_at_str = _format_timestamp_local(order_data.get('payment_request_sent_at_utc'), local_tz)
    if payment_request_at_str: lines.append(f"Payment Requested: `{payment_request_at_str}`")
    payment_received_at_str = _format_timestamp_local(order_data.get('payment_received_at_utc'), local_tz)
    if payment_received_at_str: lines.append(f"Payment Received: `{payment_received_at_str}`")
    delivering_at_str = _format_timestamp_local(order_data.get('delivering_at_utc'), local_tz)
    if delivering_at_str: lines.append(f"Delivering since: `{delivering_at_str}`")
    client_confirmed_delivery_at_str = _format_timestamp_local(order_data.get('client_confirmed_delivery_at_utc'), local_tz)
    if client_confirmed_delivery_at_str: lines.append(f"Client Confirmed Delivery: `{client_confirmed_delivery_at_str}`")
    completed_at_str = _format_timestamp_local(order_data.get('completed_at_utc'), local_tz)
    if completed_at_str: lines.append(f"Marked Completed (Admin): `{completed_at_str}`")
    lines.append("\n🛒 *Order Items:*")
    items_in_order = order_data.get('items', [])
    if items_in_order:
        for i, item_data_from_order in enumerate(items_in_order, 1):
            item_id = item_data_from_order.get('id'); full_item_info = None
            if data_manager.menu_data:
                for category_items in data_manager.menu_data.values():
                    for menu_item in category_items:
                        if menu_item.get('id') == item_id: full_item_info = menu_item; break
                    if full_item_info: break
            name_en = full_item_info.get('name_en', item_data_from_order.get('name', 'Unknown Item')) if full_item_info else item_data_from_order.get('name_en', item_data_from_order.get('name_ru', 'Item Name Missing'))
            quantity = item_data_from_order.get('quantity', 0); price = item_data_from_order.get('price', 0); item_total = price * quantity
            price_str = f"{price / 1000:.0f}K" if price % 1000 == 0 and price !=0 else str(price)
            item_total_str = f"{item_total / 1000:.0f}K" if item_total % 1000 == 0 and item_total !=0 else str(item_total)
            lines.append(f"  `{i}`. {escape_markdown(name_en)}: `{quantity}` pcs x `{price_str}` = `{item_total_str}`")
    else: lines.append("  _(empty)_")
    total_price = order_data.get('total_price', 0); original_total_price = order_data.get('original_total_price'); adjustment_amount = order_data.get('adjustment_amount', 0)
    adjustment_comment = order_data.get('adjustment_comment', ""); total_price_str = f"{total_price / 1000:.0f}K" if total_price % 1000 == 0 and total_price !=0 else str(total_price)
    lines.append("")
    if original_total_price is not None and adjustment_amount != 0 : # Показываем блок коррекции, если была коррекция
        original_total_price_str = f"{original_total_price / 1000:.0f}K" if original_total_price % 1000 == 0 and original_total_price !=0 else str(original_total_price)
        lines.append(f"Initial Sum: `{original_total_price_str}`")
        adjustment_amount_str = f"{adjustment_amount / 1000:.0f}K" if adjustment_amount % 1000 == 0 and adjustment_amount !=0 else str(adjustment_amount)
        adjustment_label = "Discount" if adjustment_amount < 0 else "Surcharge"
        lines.append(f"{adjustment_label}: `{adjustment_amount_str}`")
        if adjustment_comment: lines.append(f"Adj. Comment: _{escape_markdown(adjustment_comment)}_")
    lines.append(f"*Total Sum: `{total_price_str}`*")
    if order_data.get('is_off_hours_order', False): lines.append("Order Type: *PRE-ORDER* (off-hours)")
    lines.append("\n👤 *Client Details:*")
    lines.append(f"  Address: `{escape_markdown(str(order_data.get('address','Not specified')))}`")
    lines.append(f"  Phone: `{escape_markdown(str(order_data.get('phone','Not specified')))}`")
    client_comment = order_data.get('client_comment');
    if client_comment: lines.append(f"  Client Comment: _{escape_markdown(client_comment)}_")
    review_text = order_data.get('review_text')
    if review_text:
        review_time_str = _format_timestamp_local(order_data.get('review_timestamp_utc'), local_tz)
        lines.append("\n📝 *Client Review:*")
        if review_time_str: lines.append(f"  (Received: `{review_time_str}`)")
        lines.append(f"  _{escape_markdown(review_text)}_")
    return "\n".join(lines)

def robust_edit_message_text(bot_obj, text, chat_id, message_id, reply_markup=None, parse_mode='Markdown', new_message_if_edit_fails=True):
    try: return bot_obj.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e_edit:
        error_message_lower = str(e_edit).lower()
        if "message is not modified" in error_message_lower: return None
        print(f"Не удалось отредактировать сообщение {message_id} в чате {chat_id}: {e_edit}")
        if new_message_if_edit_fails:
            try: bot_obj.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e_del: print(f"Не удалось удалить старое сообщение {message_id}: {e_del}")
            new_msg = bot_obj.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
            user_session = data_manager.get_user_session_data(chat_id)
            if user_session.get('main_message_id') == message_id: data_manager.update_user_session_data(chat_id, 'main_message_id', new_msg.message_id)
            return new_msg
        return None

print("Модуль utils.py загружен.")