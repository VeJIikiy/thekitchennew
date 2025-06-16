# message_handlers.py
from bot_instance import bot, admin_action_prompts
# ИЗМЕНЕНИЕ: Убедимся, что client_handlers импортирован, так как он будет вызываться
import client_handlers
import admin_handlers
import data_manager
import utils
from config import ADMIN_GROUP_ID, TEXTS
import keyboards
from datetime import datetime


def handle_text_messages(message, bot_obj):
    chat_id = message.chat.id
    user_id = message.from_user.id  # Добавлено для is_sender_admin
    text = message.text.strip()

    user_session = data_manager.get_user_session_data(chat_id)  # Используем data_manager
    # current_state теперь будет безопасным, так как get_user_session_data возвращает {} по умолчанию,
    # а .get('state') на пустом словаре вернет None.
    # Поэтому проверка if current_state and ... - правильный подход.
    current_state = user_session.get('state')
    print(f"[DEBUG] Текстовое сообщение от {chat_id}. Состояние: {current_state}. Текст: {text}")

    is_sender_admin = False  # Добавлено для логики админа
    if ADMIN_GROUP_ID:
        try:
            member = bot_obj.get_chat_member(ADMIN_GROUP_ID, user_id)
            if member.status in ['creator', 'administrator']:
                is_sender_admin = True
        except Exception as e:
            print(
                f"Error checking admin status for user {user_id} in group {ADMIN_GROUP_ID} (from message_handlers): {e}")

    # Сначала обрабатываем ввод от админа, если он в состоянии ожидания
    if is_sender_admin:
        admin_prompt = admin_action_prompts.get(user_id)
        if admin_prompt:
            action = admin_prompt.get('action')
            if action == 'awaiting_adjustment_amount':
                admin_handlers.process_admin_adjustment_amount(message, bot_obj); return
            elif action == 'awaiting_adjustment_comment':
                admin_handlers.process_admin_adjustment_comment(message, bot_obj); return
            elif action == 'awaiting_admin_comment_to_client':
                admin_handlers.process_admin_comment_to_client(message, bot_obj); return
            elif action == 'awaiting_manual_cafe_status_message':
                admin_handlers.process_admin_manual_cafe_status_message(message, bot_obj); return
            elif action == 'awaiting_broadcast_message':
                admin_handlers.process_broadcast_message_text(message, bot_obj); return
            # Если у админа есть активный промпт, но он не из этого списка, пока ничего не делаем
            # Можно добавить логирование или специфическую обработку

    # Затем обрабатываем ввод от клиента
    if current_state == 'awaiting_address':  # <--- ВОЗВРАЩАЕМ ОБРАБОТКУ АДРЕСА
        client_handlers.process_address_input(message, bot_obj)
    elif current_state == 'awaiting_phone':  # <--- ВОЗВРАЩАЕМ ОБРАБОТКУ ТЕЛЕФОНА
        client_handlers.process_phone_input(message, bot_obj)
    elif current_state == 'awaiting_client_comment':  # <--- ВОЗВРАЩАЕМ ОБРАБОТКУ КОММЕНТАРИЯ К ЗАКАЗУ
        client_handlers.process_client_comment(message, bot_obj)
    elif current_state == 'awaiting_feedback_name':  # Ваша рабочая логика для обратной связи
        data_manager.update_user_session_data(chat_id, 'feedback_info', {'name': text})  # Используем data_manager
        data_manager.update_user_session_data(chat_id, 'state', 'awaiting_feedback_phone')
        bot_obj.send_message(chat_id, "Спасибо! А теперь введите ваш номер телефона:")
    elif current_state == 'awaiting_feedback_phone':  # Ваша рабочая логика для обратной связи
        feedback_info = user_session.get('feedback_info', {})
        feedback_info['phone'] = text
        data_manager.update_user_session_data(chat_id, 'feedback_info', feedback_info)
        # Следующий шаг - запрос самого сообщения обратной связи
        data_manager.update_user_session_data(chat_id, 'state', 'awaiting_feedback_message')  # НОВОЕ СОСТОЯНИЕ
        prompt_text = TEXTS.get("feedback_prompt_message", "Напишите ваше сообщение/отзыв/предложение:")
        bot_obj.send_message(chat_id, prompt_text)
        print(f"Пользователь {chat_id} ввел телефон для обратной связи: '{text}'. Ожидается сообщение.")
    elif current_state == 'awaiting_feedback_message':  # НОВЫЙ БЛОК для обработки текста сообщения обратной связи
        feedback_info = user_session.get('feedback_info', {})
        feedback_info['message'] = text

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
            feedback_message=utils.escape_markdown(text)
        )
        if ADMIN_GROUP_ID:
            try:
                bot_obj.send_message(ADMIN_GROUP_ID, admin_message_text, parse_mode='Markdown')
            except Exception as e:
                print(f"Ошибка отправки обратной связи в группу администраторов: {e}")
        else:
            print("ADMIN_GROUP_ID не настроен. Обратная связь не отправлена администраторам.")

        thanks_text = TEXTS.get("feedback_thanks", "Спасибо за вашу обратную связь! Мы ее изучим.")
        bot_obj.send_message(chat_id, thanks_text)
        data_manager.update_user_session_data(chat_id, 'state', None)  # Сброс состояния
        data_manager.update_user_session_data(chat_id, 'feedback_info', {})
        print(f"Пользователь {chat_id} завершил процесс обратной связи.")
    elif current_state and current_state.startswith('awaiting_review_text_'):  # Ваша рабочая логика для отзыва
        order_id = current_state[len('awaiting_review_text_'):]
        data_manager.update_user_session_data(chat_id, 'state', None)  # Используем data_manager
        data_manager.update_user_session_data(chat_id, 'current_order_id', None)
        thank_you_text = "Спасибо за ваш отзыв! 🌟 Мы его обязательно учтем."
        bot_obj.send_message(chat_id, thank_you_text)
        # Здесь нужно добавить сохранение отзыва в data_manager.orders и уведомление админов
        now_utc_iso = datetime.utcnow().isoformat() + "Z"
        data_manager.update_order(order_id, {'review_text': text, 'review_timestamp_utc': now_utc_iso})
        if hasattr(admin_handlers, '_update_admin_order_message'):
            admin_handlers._update_admin_order_message(bot_obj, order_id,
                                                       f"Client left a review for order #{order_id}.")
        print(f"[INFO] Получен отзыв от {chat_id} по заказу {order_id}: {text}")
    else:
        # Если это личный чат, пользователь не админ в активном состоянии, и состояние пустое
        if message.chat.type == "private" and \
                not (is_sender_admin and admin_action_prompts.get(user_id)) and \
                (current_state == "" or current_state is None):
            print(
                f"Получено необработанное текстовое сообщение от {user_id} в ЛС (состояние: '{current_state}'): '{text}'. Игнорируем и удаляем.")
            try:
                bot_obj.delete_message(chat_id, message.message_id)
            except Exception as e_del:
                print(f"Не удалось удалить сообщение пользователя {user_id}:{message.message_id} - {e_del}")


def handle_photo_messages(message, bot_obj):  # Без изменений относительно вашей последней рабочей версии
    chat_id = message.chat.id
    user_session = data_manager.get_user_session_data(chat_id)
    current_state = user_session.get('state', "")
    order_id = user_session.get('current_order_id')
    if current_state == 'awaiting_payment_photo' and order_id:
        order_data = data_manager.get_order(order_id)
        if not order_data: bot_obj.send_message(chat_id,
                                                "Ошибка: не могу найти ваш заказ для прикрепления фото чека."); return
        photo_file_id = message.photo[-1].file_id
        if hasattr(admin_handlers, 'handle_payment_receipt_photo'):
            admin_handlers.handle_payment_receipt_photo(
                bot_obj=bot_obj, order_id=order_id, client_chat_id=chat_id,
                photo_file_id=photo_file_id, client_message_id_to_update=user_session.get('main_message_id')
            )
        else:
            print("ПРЕДУПРЕЖДЕНИЕ: admin_handlers.handle_payment_receipt_photo не найден!")
            bot_obj.send_message(chat_id, "Ошибка обработки фото: функция администратора не найдена.")
    else:
        if message.chat.type == "private":
            bot_obj.send_message(chat_id,
                                 "Я получил ваше фото, но не знаю, что с ним делать сейчас. Если это чек, пожалуйста, дождитесь запроса на его отправку.")
            try:
                bot_obj.delete_message(chat_id, message.message_id)
            except Exception as e_del_photo:
                print(f"Не удалось удалить неожиданное фото от {message.from_user.id}: {e_del_photo}")


print("Модуль message_handlers.py загружен.")