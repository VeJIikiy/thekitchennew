# gsheet_manager.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime
from config import SPREADSHEET_ID
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
    if gc and clients_sheet:
        return True

    # --- НАЧАЛО ИСПРАВЛЕНИЯ: Читаем ключ из переменной окружения ---
    gcreds_json_str = os.environ.get('GCREDS_JSON')
    if not gcreds_json_str or not SPREADSHEET_ID:
        print("ПРЕДУПРЕЖДЕНИЕ GSHEET: GCREDS_JSON или SPREADSHEET_ID не настроены в переменных окружения.")
        return False

    try:
        creds_dict = json.loads(gcreds_json_str)
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        try:
            clients_sheet = spreadsheet.worksheet(CLIENTS_SHEET_NAME)
        except WorksheetNotFound:
            clients_sheet = spreadsheet.add_worksheet(title=CLIENTS_SHEET_NAME, rows="100",
                                                      cols=str(len(CLIENTS_HEADERS)))
            clients_sheet.append_row(CLIENTS_HEADERS)
        print("Google Sheets инициализирован успешно.")
        return True
    except Exception as e:
        print(f"---!!! КРИТИЧЕСКАЯ ОШИБКА ИНИЦИАЛИЗАЦИИ GOOGLE SHEETS !!!---: {e}")
        gc, clients_sheet = None, None
        return False


# ... (весь остальной код вашей функции find_or_create_client, update_client_order_info и т.д. остается без изменений) ...
# Просто оставьте ваши существующие функции здесь.

print("Модуль gsheet_manager загружен.")