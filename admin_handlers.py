# admin_handlers.py
from bot_instance import bot, admin_action_prompts
import data_manager
import keyboards
import utils
from config import ADMIN_GROUP_ID, TEXTS
import gsheet_manager
from datetime import datetime


def _update_admin_order_message(bot_obj, order_id, custom_note_for_admin="",
                                photo_file_id_explicit=None):  # Переименовал photo_file_id в photo_file_id_explicit
    order_data = data_manager.get_order(order_id)
    if not order_data:
        print(f"Could not update admin message: order {order_id} not found.")
        return

    admin_group_message_id = order_data.get('admin_group_message_id')
    admin_order_summary = utils.format_order_details_for_admin(order_data)

    if custom_note_for_admin:
        admin_order_summary = f"_{utils.escape_markdown(custom_note_for_admin)}_\n\n" + admin_order_summary

    admin_markup = keyboards.admin_order_keyboard(order_id, order_data.get('status'))

    # ИСПОЛЬЗУЕМ photo_file_id_explicit ЕСЛИ ОН ПЕРЕДАН, ИНАЧЕ БЕРЕМ ИЗ order_data
    photo_to_send = photo_file_id_explicit if photo_file_id_explicit else order_data.get('payment_photo_file_id')

    if ADMIN_GROUP_ID:
        try:
            if admin_group_message_id:
                bot_obj.delete_message(ADMIN_GROUP_ID, admin_group_message_id)
        except Exception as e_del:
            print(f"Could not delete old admin message {admin_group_message_id} for order {order_id}: {e_del}")

        try:
            if photo_to_send:  # Используем photo_to_send
                sent_msg = bot_obj.send_photo(
                    ADMIN_GROUP_ID,
                    photo_to_send,
                    caption=admin_order_summary,
                    reply_markup=admin_markup,
                    parse_mode='Markdown'
                )
                print(
                    f"Sent order {order_id} update WITH PHOTO ({'new' if photo_file_id_explicit else 'existing'}) to admin group.")
            else:
                sent_msg = bot_obj.send_message(
                    ADMIN_GROUP_ID,
                    admin_order_summary,
                    reply_markup=admin_markup,
                    parse_mode='Markdown'
                )
                print(f"Sent order {order_id} update (text-only) to admin group.")

            data_manager.update_order(order_id, {'admin_group_message_id': sent_msg.message_id})
        except Exception as e_send:
            print(f"Critical error sending order message {order_id} to admin group {ADMIN_GROUP_ID}: {e_send}")
    else:
        print(f"ADMIN_GROUP_ID not set. Order message {order_id} cannot be sent/updated.")


def handle_payment_receipt_photo(bot_obj, order_id, client_chat_id, photo_file_id, client_message_id_to_update=None):
    order_data = data_manager.get_order(order_id)
    if not order_data:
        bot_obj.send_message(client_chat_id, "Ошибка: не могу найти ваш заказ для прикрепления фото чека.")
        return

    data_manager.update_order(order_id, {
        'status': 'payment_verification',
        'payment_photo_file_id': photo_file_id,  # Сохраняем ID файла фото
        'last_updated_utc': datetime.utcnow().isoformat() + "Z"
    })

    bot_obj.send_message(client_chat_id,
                         "Спасибо! Ваше фото подтверждения оплаты получено и отправлено на проверку администратору.")
    data_manager.update_user_session_data(client_chat_id, 'state', None)

    # Передаем photo_file_id явно, чтобы _update_admin_order_message его использовал
    _update_admin_order_message(bot_obj, order_id,
                                custom_note_for_admin="Client has sent a payment receipt. Verification pending.",
                                photo_file_id_explicit=photo_file_id)

    if client_message_id_to_update:
        final_text_for_client = f"✅ Фото чека для заказа `№{order_id}` отправлено администратору на проверку.\nОжидайте подтверждения."
        utils.robust_edit_message_text(
            bot_obj, text=final_text_for_client, chat_id=client_chat_id,
            message_id=client_message_id_to_update, reply_markup=keyboards.back_to_main_menu_keyboard(),
            parse_mode='Markdown', new_message_if_edit_fails=True
        )


# --- Остальные функции handle_admin_order_callbacks, process_admin_... и т.д. ---
# Они остаются такими же, как в версии от 01 июня 2025 г., 14:10.
# Важно, что _update_admin_order_message теперь сама будет решать, прикреплять ли фото.
# Например, в handle_admin_order_callbacks:
# elif action_key == "admin_payment_recv":
#    if data_manager.update_order(order_id, {'status': 'payment_received', 'payment_received_at_utc': now_utc_iso, 'last_updated_utc': now_utc_iso}):
#        # ... уведомить клиента ...
#        _update_admin_order_message(bot_obj, order_id, "Payment received, order processing.")
#        # Здесь photo_file_id_explicit не передается, но _update_admin_order_message возьмет его из order_data, если он там есть

# (Код для handle_admin_order_callbacks и других process_... функций остается таким же, как в вашем файле от 01.06.2025, 14:08,
# так как основное изменение в _update_admin_order_message и handle_payment_receipt_photo)

# ... (Вставьте сюда остальную часть вашего файла admin_handlers.py, начиная с def handle_admin_order_callbacks(...)
# из версии, которую вы загрузили в 01 июня 2025 г., 14:08, или из моего ответа от 01 июня 2025 г., 14:10)
# Я не буду копировать его всего сюда, чтобы не делать сообщение слишком длинным,
# так как изменения касаются только _update_admin_order_message и handle_payment_receipt_photo.
# Убедитесь, что остальные функции остались нетронутыми из последней рабочей версии.

# --- КОПИЯ ОСТАЛЬНЫХ ФУНКЦИЙ ИЗ ПРЕДЫДУЩЕЙ ВЕРСИИ (01 июня 2025 г., 14:10) ---
def handle_admin_order_callbacks(call, bot_obj):  # Как в версии от 01.06.2025, 14:10
    action_full = call.data;
    parts = action_full.split('_');
    order_id_parts_start_index = -1
    if parts[0] == "admin":
        if len(parts) >= 3 and parts[1] == "adj" and parts[2] == "sum":
            order_id_parts_start_index = 3
        elif len(parts) >= 3 and parts[1] == "comment" and parts[2] == "client":
            order_id_parts_start_index = 3
        elif len(parts) >= 3 and parts[1] == "payment" and (parts[2] == "recv" or parts[2] == "reject"):
            order_id_parts_start_index = 3
        elif len(parts) >= 3 and parts[1] == "req" and parts[2] == "payment":
            order_id_parts_start_index = 3
        elif len(parts) >= 2 and parts[1] == "delivering":
            order_id_parts_start_index = 2
        elif len(parts) >= 2 and parts[1] == "completed":
            order_id_parts_start_index = 2
        elif len(parts) >= 3 and parts[1] == "cancel" and parts[2] == "order":
            order_id_parts_start_index = 3
        elif len(parts) >= 3 and parts[1] == "refresh" and parts[2] == "order":
            order_id_parts_start_index = 3
        elif len(parts) >= 2 and parts[1] == "noop":
            order_id_parts_start_index = 2
        else:
            print(f"Unknown admin order callback format: {action_full}"); return
    else:
        print(f"Non-admin callback in admin_handlers (orders): {action_full}"); return
    if order_id_parts_start_index == -1 or order_id_parts_start_index >= len(parts): print(
        f"Error extracting order ID from callback: {action_full}"); return
    order_id = "_".join(parts[order_id_parts_start_index:])
    action_key = "_".join(parts[:order_id_parts_start_index])
    try:
        bot_obj.answer_callback_query(call.id)
    except Exception:
        pass
    order_data = data_manager.get_order(order_id)
    if not order_data:
        if call.message: utils.robust_edit_message_text(bot_obj,
                                                        f"Error: Order {utils.escape_markdown(order_id)} not found.",
                                                        chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=None,
                                                        parse_mode='Markdown')
        return
    admin_user_id = call.from_user.id;
    admin_first_name = call.from_user.first_name
    group_chat_id = call.message.chat.id if call.message else ADMIN_GROUP_ID
    client_chat_id_for_order = order_data.get('client_chat_id')
    now_utc_iso = datetime.utcnow().isoformat() + "Z"
    if action_key == "admin_req_payment":
        current_total_price = order_data.get('total_price', 0)
        payment_details_template = TEXTS.get('payment_details',
                                             "Please make the payment. Amount: {total_price_formatted}")
        try:
            payment_info = payment_details_template.format(total_price_formatted=f"{current_total_price / 1000:.0f}K")
        except KeyError:
            payment_info = payment_details_template + f" Amount: {current_total_price / 1000:.0f}K"
        client_msg_ru = f"Пожалуйста, произведите оплату по заказу №{utils.escape_markdown(order_id)}.\n{payment_info}"
        if client_chat_id_for_order:
            bot_obj.send_message(client_chat_id_for_order, client_msg_ru, parse_mode='Markdown')
            data_manager.update_order(order_id,
                                      {'status': 'awaiting_payment', 'payment_request_sent_at_utc': now_utc_iso,
                                       'last_updated_utc': now_utc_iso})
            data_manager.update_user_session_data(client_chat_id_for_order, 'state', 'awaiting_payment_photo')
            data_manager.update_user_session_data(client_chat_id_for_order, 'current_order_id', order_id)
            _update_admin_order_message(bot_obj, order_id,
                                        "Payment has been requested from the client. Awaiting receipt.")
        else:
            _update_admin_order_message(bot_obj, order_id, "Error: Client chat ID not found for payment request.")
    elif action_key == "admin_adj_sum":
        admin_action_prompts[admin_user_id] = {'action': 'awaiting_adjustment_amount', 'order_id': order_id,
                                               'target_chat_id_for_reply': group_chat_id}
        admin_mention = f"@{utils.escape_markdown(call.from_user.username)}" if call.from_user.username else utils.escape_markdown(
            admin_first_name)
        prompt_text = (
            f"Order `{utils.escape_markdown(order_id)}`:\nAdministrator {admin_mention}, please enter the adjustment amount (e.g., `+50000` or `-20000`). Reply in this chat.")
        try:
            sent_prompt_msg = bot_obj.send_message(group_chat_id, prompt_text, parse_mode='Markdown')
            admin_action_prompts[admin_user_id]['prompt_message_id'] = sent_prompt_msg.message_id
        except Exception as e:
            print(f"Error sending sum request to group {group_chat_id}: {e}"); bot_obj.send_message(admin_user_id,
                                                                                                    "Could not send request to group. Please enter adjustment amount here.")
    elif action_key == "admin_comment_client":
        admin_action_prompts[admin_user_id] = {'action': 'awaiting_admin_comment_to_client', 'order_id': order_id,
                                               'target_chat_id_for_reply': group_chat_id}
        admin_mention = f"@{utils.escape_markdown(call.from_user.username)}" if call.from_user.username else utils.escape_markdown(
            admin_first_name)
        prompt_text = (
            f"Order `{utils.escape_markdown(order_id)}`:\nAdministrator {admin_mention}, please enter the comment for the client. Reply in this chat.")
        try:
            sent_prompt_msg = bot_obj.send_message(group_chat_id, prompt_text, parse_mode='Markdown')
            admin_action_prompts[admin_user_id]['prompt_message_id'] = sent_prompt_msg.message_id
        except Exception as e:
            print(f"Error sending comment request to group {group_chat_id}: {e}"); bot_obj.send_message(admin_user_id,
                                                                                                        "Could not send request to group. Please enter comment here.")
    elif action_key == "admin_payment_recv":
        if data_manager.update_order(order_id, {'status': 'payment_received', 'payment_received_at_utc': now_utc_iso,
                                                'last_updated_utc': now_utc_iso}):
            if client_chat_id_for_order: bot_obj.send_message(client_chat_id_for_order,
                                                              f"✅ Оплата по вашему заказу №{utils.escape_markdown(order_id)} подтверждена! Готовим к доставке.")
            _update_admin_order_message(bot_obj, order_id, "Payment received, order processing.")
    elif action_key == "admin_payment_reject":
        if data_manager.update_order(order_id, {'status': 'payment_rejected', 'last_updated_utc': now_utc_iso}):
            if client_chat_id_for_order: bot_obj.send_message(client_chat_id_for_order,
                                                              f"⚠️ По вашему заказу №{utils.escape_markdown(order_id)} возникла проблема с оплатой. Администратор скоро свяжется с вами или уже оставил комментарий.")
            _update_admin_order_message(bot_obj, order_id,
                                        "Payment rejected by admin. Client may need to be contacted.")
    elif action_key == "admin_delivering":
        if data_manager.update_order(order_id, {'status': 'delivering', 'delivering_at_utc': now_utc_iso,
                                                'last_updated_utc': now_utc_iso}):
            if client_chat_id_for_order:
                bot_obj.send_message(client_chat_id_for_order,
                                     f"🛵 Ваш заказ №{utils.escape_markdown(order_id)} передан в доставку!")
                delivery_confirmation_markup = keyboards.client_confirm_delivery_keyboard(order_id)
                bot_obj.send_message(client_chat_id_for_order,
                                     "Пожалуйста, нажмите кнопку ниже, когда получите ваш заказ.",
                                     reply_markup=delivery_confirmation_markup)
            _update_admin_order_message(bot_obj, order_id, "Order is out for delivery.")
    elif action_key == "admin_completed":
        order_completed_payload = {'status': 'completed', 'completed_at_utc': now_utc_iso,
                                   'last_updated_utc': now_utc_iso}
        if order_data.get('status') == 'client_confirmed_delivery':
            _update_admin_order_message(bot_obj, order_id, "Order completed (client had confirmed delivery).")
            if data_manager.update_order(order_id, order_completed_payload):
                if client_chat_id_for_order:
                    if data_manager.get_user_session_data(client_chat_id_for_order).get('state') != None:
                        data_manager.clear_user_order_session(client_chat_id_for_order)
        else:
            if data_manager.update_order(order_id, order_completed_payload):
                if client_chat_id_for_order:
                    bot_obj.send_message(client_chat_id_for_order,
                                         f"🎉 Ваш заказ №{utils.escape_markdown(order_id)} выполнен! Спасибо, что выбрали нас!")
                    data_manager.update_user_session_data(client_chat_id_for_order, 'state',
                                                          f'awaiting_review_text_{order_id}')
                    data_manager.update_user_session_data(client_chat_id_for_order, 'current_order_id', order_id)
                    review_prompt_text = TEXTS.get("ask_for_review", "Пожалуйста, оставьте ваш отзыв о заказе.")
                    bot_obj.send_message(client_chat_id_for_order, review_prompt_text)
                _update_admin_order_message(bot_obj, order_id, "Order completed. Review requested from client.")
    elif action_key == "admin_cancel_order":
        if data_manager.update_order(order_id, {'status': 'cancelled_by_admin', 'last_updated_utc': now_utc_iso}):
            if client_chat_id_for_order: bot_obj.send_message(client_chat_id_for_order,
                                                              f"❌ К сожалению, ваш заказ №{utils.escape_markdown(order_id)} был отменен администратором.")
            _update_admin_order_message(bot_obj, order_id, "Order cancelled by admin.")
            if client_chat_id_for_order: data_manager.clear_user_order_session(client_chat_id_for_order)
    elif action_key == "admin_refresh_order":
        photo_to_attach = order_data.get('payment_photo_file_id')
        _update_admin_order_message(bot_obj, order_id, "Order information refreshed.",
                                    photo_file_id_explicit=photo_to_attach)
    elif action_key == "admin_noop":
        pass


def process_admin_adjustment_amount(message, bot_obj):  # Как в версии от 01.06.2025, 13:37
    admin_replied_id = message.from_user.id
    prompt_data = admin_action_prompts.get(admin_replied_id)
    if not prompt_data or prompt_data.get('action') != 'awaiting_adjustment_amount': return
    order_id = prompt_data['order_id'];
    amount_text = message.text.strip()
    target_chat_id_for_reply = prompt_data.get('target_chat_id_for_reply', ADMIN_GROUP_ID)
    prompt_message_id_to_delete = prompt_data.get('prompt_message_id')
    try:
        if prompt_message_id_to_delete and target_chat_id_for_reply: bot_obj.delete_message(target_chat_id_for_reply,
                                                                                            prompt_message_id_to_delete)
    except Exception as e:
        print(f"Could not delete sum prompt message {prompt_message_id_to_delete}: {e}")
    try:
        bot_obj.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Could not delete admin sum message: {e}")
    try:
        if amount_text.lower().endswith('k'):
            adjustment_amount = int(float(amount_text[:-1].replace(',', '.')) * 1000)
        else:
            adjustment_amount = int(float(amount_text.replace(',', '.')))
        admin_action_prompts[admin_replied_id]['adjustment_amount'] = adjustment_amount
        admin_action_prompts[admin_replied_id]['action'] = 'awaiting_adjustment_comment'
        admin_mention = f"@{utils.escape_markdown(message.from_user.username)}" if message.from_user.username else utils.escape_markdown(
            message.from_user.first_name)
        next_prompt_text = (
            f"Adjustment amount for order `{utils.escape_markdown(order_id)}`: `{adjustment_amount}`.\nAdministrator {admin_mention}, now enter a comment for the client (or `-` if no comment). Reply in this chat.")
        sent_next_prompt = bot_obj.send_message(target_chat_id_for_reply, next_prompt_text, parse_mode='Markdown')
        admin_action_prompts[admin_replied_id]['prompt_message_id'] = sent_next_prompt.message_id
    except ValueError:
        bot_obj.send_message(target_chat_id_for_reply, "Invalid amount format. Please try 'Adjust Sum' again.")
        if admin_replied_id in admin_action_prompts: del admin_action_prompts[admin_replied_id]


def process_admin_adjustment_comment(message, bot_obj):  # Как в версии от 01.06.2025, 13:37
    admin_replied_id = message.from_user.id
    prompt_data = admin_action_prompts.get(admin_replied_id)
    if not prompt_data or prompt_data.get('action') != 'awaiting_adjustment_comment': return
    order_id = prompt_data['order_id'];
    adjustment_amount = prompt_data.get('adjustment_amount', 0)
    adjustment_comment_text = message.text.strip()
    if adjustment_comment_text == '-': adjustment_comment_text = ""
    target_chat_id_for_reply = prompt_data.get('target_chat_id_for_reply', ADMIN_GROUP_ID)
    prompt_message_id_to_delete = prompt_data.get('prompt_message_id')
    try:
        if prompt_message_id_to_delete and target_chat_id_for_reply: bot_obj.delete_message(target_chat_id_for_reply,
                                                                                            prompt_message_id_to_delete)
    except Exception as e:
        print(f"Could not delete comment prompt message {prompt_message_id_to_delete}: {e}")
    try:
        bot_obj.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Could not delete admin comment message: {e}")
    order_data = data_manager.get_order(order_id)
    if not order_data:
        if target_chat_id_for_reply: bot_obj.send_message(target_chat_id_for_reply,
                                                          f"Error: Order {utils.escape_markdown(order_id)} not found.")
        if admin_replied_id in admin_action_prompts: del admin_action_prompts[admin_replied_id]; return
    original_total = order_data.get('original_total_price', order_data.get('total_price', 0))
    new_total_price = original_total + adjustment_amount;
    client_chat_id_for_order = order_data.get('client_chat_id')
    now_utc_iso = datetime.utcnow().isoformat() + "Z"
    update_payload = {'total_price': new_total_price, 'original_total_price': original_total,
                      'adjustment_amount': adjustment_amount, 'adjustment_comment': adjustment_comment_text,
                      'status': 'awaiting_payment', 'last_updated_utc': now_utc_iso,
                      'payment_request_sent_at_utc': now_utc_iso}
    if data_manager.update_order(order_id, update_payload):
        client_msg = f"🔔 Администратор внес изменения в ваш заказ №{utils.escape_markdown(order_id)}.\n"
        if adjustment_amount != 0: adj_type = "Скидка" if adjustment_amount < 0 else "Надбавка"; client_msg += f"{adj_type}: {abs(adjustment_amount) / 1000:.0f}K\n"
        if adjustment_comment_text: client_msg += f"Комментарий администратора: {utils.escape_markdown(adjustment_comment_text)}\n"
        payment_details_template = TEXTS.get('payment_details', "Реквизиты: ... Сумма: {total_price_formatted}")
        try:
            payment_info = payment_details_template.format(total_price_formatted=f"{new_total_price / 1000:.0f}K")
        except KeyError:
            payment_info = payment_details_template + f" Сумма: {new_total_price / 1000:.0f}K"
        client_msg += f"\n*Новая сумма к оплате: {new_total_price / 1000:.0f}K*\n{payment_info}"
        if client_chat_id_for_order:
            bot_obj.send_message(client_chat_id_for_order, client_msg, parse_mode='Markdown')
            data_manager.update_user_session_data(client_chat_id_for_order, 'state', 'awaiting_payment_photo')
            data_manager.update_user_session_data(client_chat_id_for_order, 'current_order_id', order_id)
            print(
                f"Set state 'awaiting_payment_photo' and current_order_id='{order_id}' for client {client_chat_id_for_order}")
        if target_chat_id_for_reply: bot_obj.send_message(target_chat_id_for_reply,
                                                          f"Amount for order {utils.escape_markdown(order_id)} adjusted. Client notified.")
        _update_admin_order_message(bot_obj, order_id,
                                    f"Sum adjusted by {message.from_user.first_name}. Client notified.")
    if admin_replied_id in admin_action_prompts: del admin_action_prompts[admin_replied_id]


def process_admin_comment_to_client(message, bot_obj):  # Как в версии от 01.06.2025, 13:37
    admin_replied_id = message.from_user.id;
    prompt_data = admin_action_prompts.get(admin_replied_id)
    if not prompt_data or prompt_data.get('action') != 'awaiting_admin_comment_to_client': return
    order_id = prompt_data['order_id'];
    admin_comment_text = message.text.strip()
    target_chat_id_for_reply = prompt_data.get('target_chat_id_for_reply', ADMIN_GROUP_ID)
    prompt_message_id_to_delete = prompt_data.get('prompt_message_id')
    try:
        if prompt_message_id_to_delete and target_chat_id_for_reply: bot_obj.delete_message(target_chat_id_for_reply,
                                                                                            prompt_message_id_to_delete)
    except Exception as e:
        print(f"Could not delete admin comment prompt: {e}")
    try:
        bot_obj.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Could not delete admin comment message: {e}")
    order_data = data_manager.get_order(order_id)
    if not order_data:
        if target_chat_id_for_reply: bot_obj.send_message(target_chat_id_for_reply,
                                                          f"Error: Order {utils.escape_markdown(order_id)} not found.")
        if admin_replied_id in admin_action_prompts: del admin_action_prompts[admin_replied_id]; return
    current_admin_comments = order_data.get('admin_comments', []);
    admin_name = message.from_user.first_name or f"Admin ({admin_replied_id})"
    current_admin_comments.append(f"{admin_name}: {admin_comment_text}");
    client_chat_id_for_order = order_data.get('client_chat_id')
    if data_manager.update_order(order_id, {'admin_comments': current_admin_comments,
                                            'last_updated_utc': datetime.utcnow().isoformat() + "Z"}):
        if client_chat_id_for_order: bot_obj.send_message(client_chat_id_for_order,
                                                          f"💬 Администратор ({utils.escape_markdown(admin_name)}) оставил комментарий к вашему заказу №{utils.escape_markdown(order_id)}:\n_{utils.escape_markdown(admin_comment_text)}_",
                                                          parse_mode='Markdown')
        if target_chat_id_for_reply: bot_obj.send_message(target_chat_id_for_reply,
                                                          f"Comment for order {utils.escape_markdown(order_id)} added.")
        _update_admin_order_message(bot_obj, order_id, f"Comment added by {admin_name}.")
    if admin_replied_id in admin_action_prompts: del admin_action_prompts[admin_replied_id]


def handle_admin_cafe_status_callbacks(call, bot_obj):  # Как в версии от 01.06.2025, 13:37
    admin_user_id = call.from_user.id;
    group_chat_id = call.message.chat.id if call.message else ADMIN_GROUP_ID
    try:
        bot_obj.answer_callback_query(call.id)
    except Exception:
        pass
    action = call.data
    if action in ["admin_cafe_manual_open", "admin_cafe_manual_close"]:
        new_status = 'manual_open' if action == "admin_cafe_manual_open" else 'manual_close'
        admin_action_prompts[admin_user_id] = {'action': 'awaiting_manual_cafe_status_message',
                                               'new_status_to_set': new_status,
                                               'target_chat_id_for_reply': group_chat_id,
                                               'admin_group_message_id': call.message.message_id if call.message else None}
        admin_mention = f"@{utils.escape_markdown(call.from_user.username)}" if call.from_user.username else utils.escape_markdown(
            call.from_user.first_name)
        prompt_text = "Cafe will be set to OPEN (manual override)." if new_status == 'manual_open' else "Cafe will be set to CLOSED (manual override)."
        prompt_text += (
            f"\nAdministrator {admin_mention}, would you like to add a message for clients (e.g., 'Open until 23:00')? Enter text or `-` to skip. Reply in this chat.")
        try:
            sent_prompt_msg = bot_obj.send_message(group_chat_id, prompt_text, parse_mode='Markdown')
            admin_action_prompts[admin_user_id]['prompt_message_id'] = sent_prompt_msg.message_id
        except Exception as e:
            print(f"Error sending status prompt to group {group_chat_id}: {e}"); bot_obj.send_message(admin_user_id,
                                                                                                      "Could not send request to group. Please enter status message here.")
    elif action == "admin_cafe_auto":
        if data_manager.set_cafe_status('auto'): _send_updated_cafe_status_to_admin_group(bot_obj, group_chat_id,
                                                                                          call.message.message_id if call.message else None,
                                                                                          "Cafe set to automatic schedule mode.")


def process_admin_manual_cafe_status_message(message, bot_obj):  # Как в версии от 01.06.2025, 13:37
    admin_replied_id = message.from_user.id
    prompt_data = admin_action_prompts.get(admin_replied_id)
    if not prompt_data or prompt_data.get('action') != 'awaiting_manual_cafe_status_message': return
    new_status = prompt_data['new_status_to_set'];
    admin_group_msg_id_to_update = prompt_data.get('admin_group_message_id')
    admin_input_message = message.text.strip();
    manual_message_for_clients = admin_input_message if admin_input_message != '-' else None
    target_chat_id_for_reply = prompt_data.get('target_chat_id_for_reply', ADMIN_GROUP_ID);
    prompt_message_id_to_delete = prompt_data.get('prompt_message_id')
    try:
        if prompt_message_id_to_delete and target_chat_id_for_reply: bot_obj.delete_message(target_chat_id_for_reply,
                                                                                            prompt_message_id_to_delete)
    except Exception:
        pass
    try:
        bot_obj.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    if data_manager.set_cafe_status(new_status, manual_message=manual_message_for_clients):
        note = "Cafe status updated.";
        if manual_message_for_clients: note += f" Client message: '{manual_message_for_clients}'"
        _send_updated_cafe_status_to_admin_group(bot_obj, ADMIN_GROUP_ID, admin_group_msg_id_to_update, note)
        if target_chat_id_for_reply: bot_obj.send_message(target_chat_id_for_reply,
                                                          f"Cafe status successfully changed to '{new_status}' by administrator {utils.escape_markdown(message.from_user.first_name)}.")
    if admin_replied_id in admin_action_prompts: del admin_action_prompts[admin_replied_id]


def _send_updated_cafe_status_to_admin_group(bot_obj, chat_id_to_update_buttons, message_id_to_update_buttons,
                                             admin_note):  # Как в версии от 01.06.2025, 13:37
    status_details = utils.get_cafe_operational_status_details()
    text_for_group_update = f"*Cafe Status Updated!* ({utils.escape_markdown(admin_note)})\\n\\n{status_details['status_line']}{status_details['schedule_text']}"
    markup = keyboards.admin_cafe_status_keyboard()
    if str(chat_id_to_update_buttons) == str(ADMIN_GROUP_ID) and message_id_to_update_buttons:
        utils.robust_edit_message_text(bot_obj, text_for_group_update, chat_id=ADMIN_GROUP_ID,
                                       message_id=message_id_to_update_buttons, reply_markup=markup,
                                       parse_mode='Markdown')
    elif ADMIN_GROUP_ID:
        bot_obj.send_message(ADMIN_GROUP_ID, text_for_group_update, reply_markup=markup, parse_mode='Markdown')
    else:
        print("ADMIN_GROUP_ID not set, cannot send updated cafe status.")


def send_cafe_status_management_menu(message, bot_obj):  # Как в версии от 01.06.2025, 13:37
    status_details = utils.get_cafe_operational_status_details()
    text = f"*Cafe Status Management*\\n\\nCurrent Status:\\n{status_details['status_line']}{status_details['schedule_text']}\\n\\nSelect action:"
    markup = keyboards.admin_cafe_status_keyboard()
    bot_obj.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')


def prompt_for_broadcast_message(admin_chat_id, bot_obj):  # Как в версии от 01.06.2025, 13:37
    admin_action_prompts[admin_chat_id] = {'action': 'awaiting_broadcast_message'}
    bot_obj.send_message(admin_chat_id, "Enter broadcast message text for all users:")
    print(f"Admin {admin_chat_id} initiated broadcast.")


def process_broadcast_message_text(message, bot_obj):  # Как в версии от 01.06.2025, 13:37
    admin_user_id = message.from_user.id;
    broadcast_text = message.text
    if not broadcast_text: bot_obj.send_message(admin_user_id, "Broadcast message cannot be empty."); return
    admin_action_prompts[admin_user_id] = {'action': 'awaiting_broadcast_confirmation', 'message_text': broadcast_text}
    try:
        bot_obj.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    confirmation_text = (
        f"Send the following broadcast message?\\n\\n---\\n{utils.escape_markdown(broadcast_text)}\\n---")
    markup = keyboards.confirm_action_keyboard("admin_broadcast_send", "admin_broadcast_cancel", "✅ Yes, send",
                                               "❌ No, cancel", lang="en")
    bot_obj.send_message(admin_user_id, confirmation_text, reply_markup=markup, parse_mode='Markdown')
    print(f"Broadcast confirmation sent to admin {admin_user_id}.")


def handle_broadcast_callbacks(call, bot_obj):  # Как в версии от 01.06.2025, 13:37
    admin_user_id = call.from_user.id
    prompt_data = admin_action_prompts.get(admin_user_id)
    if not prompt_data or prompt_data.get('action') != 'awaiting_broadcast_confirmation':
        try:
            bot_obj.answer_callback_query(call.id, "Invalid state.", show_alert=True); return
        except Exception:
            pass
    try:
        bot_obj.answer_callback_query(call.id)
    except Exception:
        pass
    try:
        bot_obj.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          reply_markup=None)
    except Exception:
        pass
    if call.data == "admin_broadcast_send":
        message_text_to_send = prompt_data.get('message_text')
        if not message_text_to_send: bot_obj.send_message(admin_user_id,
                                                          "Error: Broadcast text not found.");_clear_admin_prompt(
            admin_user_id); return
        bot_obj.send_message(admin_user_id, "Starting broadcast...")
        user_ids = [];
        try:
            if gsheet_manager and hasattr(gsheet_manager,
                                          'get_all_client_ids'): user_ids = gsheet_manager.get_all_client_ids()
        except Exception as e:
            print(f"Error getting IDs from GSheets: {e}")
        if not user_ids and data_manager.user_data: user_ids = list(data_manager.user_data.keys())
        user_ids = list(set(user_ids))
        if not user_ids: bot_obj.send_message(admin_user_id, "No users to broadcast to."); _clear_admin_prompt(
            admin_user_id); return
        s, f = 0, 0
        for uid_str in user_ids:
            try:
                uid = int(uid_str)
                if str(uid) == str(ADMIN_GROUP_ID): continue
                bot_obj.send_message(uid, message_text_to_send, parse_mode='Markdown');
                s += 1
            except Exception as e_send:
                f += 1; print(f"Error sending to user {uid_str}: {e_send}")
        bot_obj.send_message(admin_user_id, f"Broadcast finished. Sent: {s}, Failed: {f}")
    elif call.data == "admin_broadcast_cancel":
        bot_obj.send_message(admin_user_id, "Broadcast cancelled.")
    _clear_admin_prompt(admin_user_id)


def _clear_admin_prompt(admin_user_id):
    if admin_user_id in admin_action_prompts: del admin_action_prompts[admin_user_id]


print("Модуль admin_handlers.py загруввжен.")