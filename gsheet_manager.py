# gsheet_manager.py
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import SERVICE_ACCOUNT_FILE, SPREADSHEET_ID
# ИЗМЕНЕНИЕ: Импортируем только WorksheetNotFound, CellNotFound будем ловить через общее исключение gspread
from gspread.exceptions import WorksheetNotFound, GSpreadException

CLIENTS_SHEET_NAME = 'Клиенты'
CLIENTS_HEADERS = [
    'ClientID', 'TelegramName', 'PhoneNumber', 'FirstContactDate',
    'LastOrderDate', 'TotalOrdersCount', 'TotalSpent',
    'MailingListOptIn', 'OptInDate', 'Notes'
]

gc = None
clients_sheet = None


def _init_gsheets():
    global gc, clients_sheet
    if gc and clients_sheet: return True

    if not SERVICE_ACCOUNT_FILE or not SPREADSHEET_ID or SPREADSHEET_ID == 'ВАШ_ID_GOOGLE_ТАБЛИЦЫ_СЮДА':
        print("ПРЕДУПРЕЖДЕНИЕ GSHEET: SERVICE_ACCOUNT_FILE или SPREADSHEET_ID не настроены.")
        return False

    print(f"Попытка инициализации Google Sheets: Файл ключа='{SERVICE_ACCOUNT_FILE}', ID Таблицы='{SPREADSHEET_ID}'")
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets',
                  'https://www.googleapis.com/auth/drive.file']
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
        gc = gspread.authorize(creds)
        print(f"Авторизация через gspread.authorize() с Credentials успешна. Тип gc: {type(gc)}")

        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        print(f"Таблица '{SPREADSHEET_ID}' успешно открыта: '{spreadsheet.title}'")

        try:
            clients_sheet = spreadsheet.worksheet(CLIENTS_SHEET_NAME)
            print(f"Лист '{CLIENTS_SHEET_NAME}' найден.")
            current_headers = clients_sheet.row_values(1)
            if current_headers != CLIENTS_HEADERS:
                print(f"ПРЕДУПРЕЖДЕНИЕ GSHEET: Заголовки в листе '{CLIENTS_SHEET_NAME}' не совпадают!")
        except WorksheetNotFound:
            print(f"Лист '{CLIENTS_SHEET_NAME}' не найден. Попытка создать...")
            clients_sheet = spreadsheet.add_worksheet(title=CLIENTS_SHEET_NAME, rows="100",
                                                      cols=str(len(CLIENTS_HEADERS)))
            clients_sheet.append_row(CLIENTS_HEADERS)
            print(f"Лист '{CLIENTS_SHEET_NAME}' создан с заголовками.")
        print("Google Sheets инициализирован успешно.")
        return True
    except AttributeError as e_attr:
        print(f"---!!! ОШИБКА ИНИЦИАЛИЗАЦИИ GOOGLE SHEETS (AttributeError) !!!---");
        print(f"Сообщение: {e_attr}")
        if 'gc' in locals() and gc is not None: print(f"Отладка: Тип объекта gc: {type(gc)}, dir: {dir(gc)}")
        gc = None;
        clients_sheet = None;
        return False
    except Exception as e:
        print(f"---!!! НЕПРЕДВИДЕННАЯ ОШИБКА ИНИЦИАЛИЗАЦИИ GOOGLE SHEETS !!!---");
        print(f"Тип: {type(e).__name__}, Сообщение: {e}")
        import traceback;
        traceback.print_exc();
        gc = None;
        clients_sheet = None;
        return False


def find_or_create_client(client_id, client_name, phone_number=None):
    if not _init_gsheets() or not clients_sheet: return None
    client_id_str = str(client_id)
    try:
        cell = clients_sheet.find(client_id_str, in_column=CLIENTS_HEADERS.index('ClientID') + 1)
        # Если find ничего не нашел, в новых версиях gspread он вызывает CellNotFound (которое наследуется от GSpreadException)
        # Для старых версий он мог вернуть None. Добавим проверку на None для совместимости.
        if cell is None:
            raise GSpreadException(
                f"Cell not found for ClientID: {client_id_str}")  # Инициируем общее исключение gspread

        row_number = cell.row
        print(f"Клиент {client_id_str} найден в Google Sheets, строка {row_number}.")
        current_name = clients_sheet.cell(row_number, CLIENTS_HEADERS.index('TelegramName') + 1).value
        if client_name and current_name != client_name: clients_sheet.update_cell(row_number, CLIENTS_HEADERS.index(
            'TelegramName') + 1, client_name)
        if phone_number: clients_sheet.update_cell(row_number, CLIENTS_HEADERS.index('PhoneNumber') + 1, phone_number)
        return row_number
    except GSpreadException:  # ИЗМЕНЕНИЕ: Ловим общее GSpreadException, которое включает CellNotFound
        print(f"Клиент {client_id_str} не найден (или другая ошибка gspread). Создание новой записи...")
        now_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S");
        new_row_data = [''] * len(CLIENTS_HEADERS)
        new_row_data[CLIENTS_HEADERS.index('ClientID')] = client_id_str
        new_row_data[CLIENTS_HEADERS.index('TelegramName')] = client_name or ""
        new_row_data[CLIENTS_HEADERS.index('PhoneNumber')] = phone_number or ""
        new_row_data[CLIENTS_HEADERS.index('FirstContactDate')] = now_date_str
        new_row_data[CLIENTS_HEADERS.index('TotalOrdersCount')] = 0
        new_row_data[CLIENTS_HEADERS.index('TotalSpent')] = 0
        new_row_data[CLIENTS_HEADERS.index('MailingListOptIn')] = ""
        clients_sheet.append_row(new_row_data);
        print(f"Новый клиент {client_id_str} добавлен.");
        return clients_sheet.row_count
    except Exception as e:
        print(f"Ошибка при поиске/создании клиента {client_id_str}: {e}"); return None


def update_client_order_info(client_id, order_value):
    if not _init_gsheets() or not clients_sheet: return
    client_id_str = str(client_id)
    try:
        cell = clients_sheet.find(client_id_str, in_column=CLIENTS_HEADERS.index('ClientID') + 1)
        if cell is None: raise GSpreadException(f"Cell not found for ClientID during order update: {client_id_str}")
        row_number = cell.row
        now_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clients_sheet.update_cell(row_number, CLIENTS_HEADERS.index('LastOrderDate') + 1, now_date_str)
        current_count_str = clients_sheet.cell(row_number, CLIENTS_HEADERS.index('TotalOrdersCount') + 1).value
        current_count = int(current_count_str) if str(current_count_str).isdigit() else 0
        clients_sheet.update_cell(row_number, CLIENTS_HEADERS.index('TotalOrdersCount') + 1, current_count + 1)
        current_spent_str = clients_sheet.cell(row_number, CLIENTS_HEADERS.index('TotalSpent') + 1).value
        try:
            current_spent = float(str(current_spent_str).replace(',', '.')) if current_spent_str else 0.0
        except ValueError:
            current_spent = 0.0
        clients_sheet.update_cell(row_number, CLIENTS_HEADERS.index('TotalSpent') + 1,
                                  current_spent + float(order_value))
        print(f"Обновлена информация о заказах для клиента {client_id_str}.")
    except GSpreadException:
        print(f"Клиент {client_id_str} не найден для обновления инфо о заказе (или ошибка gspread).")
    except Exception as e:
        print(f"Ошибка обновления инфо о заказах клиента {client_id_str}: {e}")


def update_mailing_opt_in(client_id, opt_in_status: bool):
    if not _init_gsheets() or not clients_sheet: return
    client_id_str = str(client_id)
    try:
        cell = clients_sheet.find(client_id_str, in_column=CLIENTS_HEADERS.index('ClientID') + 1)
        if cell is None: raise GSpreadException(f"Cell not found for ClientID during mailing opt-in: {client_id_str}")
        row_number = cell.row
        status_str = "Да" if opt_in_status else "Нет";
        now_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clients_sheet.update_cell(row_number, CLIENTS_HEADERS.index('MailingListOptIn') + 1, status_str)
        clients_sheet.update_cell(row_number, CLIENTS_HEADERS.index('OptInDate') + 1, now_date_str)
        print(f"Обновлен статус подписки для клиента {client_id_str} на '{status_str}'.")
    except GSpreadException:
        print(f"Клиент {client_id_str} не найден для обновления статуса подписки (или ошибка gspread).")
    except Exception as e:
        print(f"Ошибка обновления статуса подписки клиента {client_id_str}: {e}")


def get_all_client_ids():
    if not _init_gsheets() or not clients_sheet: return []
    try:
        client_id_column_index = CLIENTS_HEADERS.index('ClientID') + 1
        all_ids_with_header = clients_sheet.col_values(client_id_column_index)
        if not all_ids_with_header or len(all_ids_with_header) <= 1: return []
        client_ids = [str(id_val).strip() for id_val in all_ids_with_header[1:] if str(id_val).strip()]
        return client_ids
    except Exception as e:
        print(f"Ошибка при получении ClientID из Google Sheets: {e}"); return []


print("Модуль gsheet_manager загружен.")