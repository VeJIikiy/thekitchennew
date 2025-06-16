# data_manager.py
import json
import os
from datetime import datetime

MENU_FILE = 'menu_ru.json'
CAFE_STATUS_FILE = 'cafe_status.json'
ORDER_NUMBER_FILE = 'current_order_number.json'

menu_data = {}
user_data = {}
orders = {}
cafe_operational_status = {'status': 'auto', 'manual_message': None}
current_order_number = 0

def load_all_data():
    global current_order_number
    print("Инициализация данных (data_manager.py)...")
    _load_menu()
    _load_cafe_status()
    _load_current_order_number()
    print("Данные инициализированы.")

def _load_menu():
    global menu_data
    if os.path.exists(MENU_FILE):
        try:
            with open(MENU_FILE, 'r', encoding='utf-8') as f:
                menu_data = json.load(f)
            print(f"Меню загружено из {MENU_FILE}")
        except Exception as e:
            print(f"Ошибка загрузки меню из {MENU_FILE}: {e}. Меню будет пустым.")
            menu_data = {}
    else:
        print(f"Файл меню {MENU_FILE} не найден. Меню будет пустым.")
        menu_data = {}

def _load_cafe_status():
    global cafe_operational_status
    if os.path.exists(CAFE_STATUS_FILE):
        try:
            with open(CAFE_STATUS_FILE, 'r', encoding='utf-8') as f:
                loaded_status = json.load(f)
                if isinstance(loaded_status, dict) and 'status' in loaded_status:
                    cafe_operational_status = loaded_status
                print(f"Статус кафе загружен: {cafe_operational_status}")
        except Exception as e:
            print(f"Ошибка загрузки статуса кафе: {e}. Используется статус по умолчанию.")
            cafe_operational_status = {'status': 'auto', 'manual_message': None}
    else:
        print(f"Файл {CAFE_STATUS_FILE} не найден. Используется статус кафе по умолчанию ('auto').")
        save_cafe_status()

def save_cafe_status():
    try:
        with open(CAFE_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(cafe_operational_status, f, ensure_ascii=False, indent=4)
        print(f"Статус кафе сохранен: {cafe_operational_status}")
    except Exception as e:
        print(f"Ошибка сохранения статуса кафе: {e}")

def get_cafe_status():
    return cafe_operational_status.copy()

def set_cafe_status(new_status, manual_message=None):
    global cafe_operational_status
    if new_status in ['auto', 'manual_open', 'manual_close']:
        cafe_operational_status['status'] = new_status
        cafe_operational_status['manual_message'] = manual_message if new_status != 'auto' else None
        save_cafe_status()
        return True
    return False

def _load_current_order_number():
    global current_order_number
    if os.path.exists(ORDER_NUMBER_FILE):
        try:
            with open(ORDER_NUMBER_FILE, 'r') as f:
                data = json.load(f)
                current_order_number = data.get('last_order_number', 0)
        except Exception as e:
            print(f"Ошибка загрузки номера заказа: {e}. Установлен 0.")
            current_order_number = 0
    else:
        current_order_number = 0
        _save_current_order_number()
    print(f"Текущий номер для ID заказа: {current_order_number}")

def _save_current_order_number():
    try:
        with open(ORDER_NUMBER_FILE, 'w') as f:
            json.dump({'last_order_number': current_order_number}, f, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения номера заказа: {e}")

def generate_new_order_id():
    global current_order_number
    current_order_number += 1
    _save_current_order_number()
    date_str = datetime.now().strftime("%Y%m%d")
    return f"TK-{date_str}-{current_order_number:05d}"

def get_user_session_data(chat_id):
    return user_data.get(str(chat_id), {})

def update_user_session_data(chat_id, data_key, value):
    str_chat_id = str(chat_id)
    if str_chat_id not in user_data:
        user_data[str_chat_id] = {}
    user_data[str_chat_id][data_key] = value

def init_user_order_session(chat_id):
    str_chat_id = str(chat_id)
    user_data[str_chat_id] = {
        'current_order_id': None, 'cart': [], 'viewed_removed_items': [],
        'state': None, 'main_message_id': None
    }
    print(f"Сессия заказа инициализирована/сброшена для chat_id: {str_chat_id}")

def clear_user_order_session(chat_id):
    str_chat_id = str(chat_id)
    if str_chat_id in user_data:
        init_user_order_session(str_chat_id)
        print(f"Сессия заказа очищена для chat_id: {str_chat_id}")

def create_new_order(chat_id, user_name):
    order_id = generate_new_order_id()
    now_utc_iso = datetime.utcnow().isoformat() + "Z"
    orders[order_id] = {
        'order_id': order_id, 'client_chat_id': chat_id, 'client_name': user_name,
        'created_at_utc': now_utc_iso, 'items': [], 'total_price': 0,
        'original_total_price': None, 'adjustment_amount': 0, 'adjustment_comment': None,
        'address': None, 'phone': None, 'status': 'pending_client_info',
        'client_comment': None, 'admin_comments': [], 'viewed_removed_items_final': [],
        'is_off_hours_order': False, 'payment_photo_file_id': None,
        'admin_group_message_id': None, 'finalized_at_utc': None,
        'payment_request_sent_at_utc': None, # Для отслеживания, когда запросили оплату
        'payment_received_at_utc': None, 'delivering_at_utc': None,
        'client_confirmed_delivery_at_utc': None, # Когда клиент подтвердил доставку
        'completed_at_utc': None, 'review_text': None, 'review_timestamp_utc': None,
        'last_updated_utc': now_utc_iso
    }
    update_user_session_data(chat_id, 'current_order_id', order_id)
    print(f"Создан новый заказ: {order_id} для клиента {user_name} ({chat_id})")
    return order_id

def get_order(order_id):
    return orders.get(order_id)

def update_order(order_id, update_data_dict):
    if order_id in orders:
        update_data_dict['last_updated_utc'] = datetime.utcnow().isoformat() + "Z"
        orders[order_id].update(update_data_dict)
        print(f"Заказ {order_id} обновлен: {update_data_dict}")
        return True
    print(f"Не удалось обновить заказ {order_id}: не найден.")
    return False

print("Модуль data_manager загружен.")