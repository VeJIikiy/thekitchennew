import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID'))
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

CAFE_SCHEDULE = {
    'weekdays': {'open': '08:00', 'close': '20:00'},
    'saturday': {'open': '08:00', 'close': '20:00'},
    'sunday': {'open': '08:00', 'close': '20:00'}
}

DEFAULT_TIMEZONE = 'Asia/Makassar'
WELCOME_IMAGE_PATH = 'welcome_image.png'
SERVICE_ACCOUNT_FILE = 'service_account.json'

TEXTS = {
    "cafe_closed_can_preorder": "К сожалению, кафе сейчас закрыто.\nХотите оформить заказ сейчас? Мы примем его и обработаем, как только начнем работать.",
    "phone_invalid": "Номер телефона введен некорректно. Пожалуйста, убедитесь, что он содержит не менее 10 цифр и не имеет букв (допустим + в начале). Попробуйте еще раз.",
    "order_take_phone": "Пожалуйста, укажите ваш контактный номер телефона (например, WhatsApp) для связи и подтверждения заказа:",
    "order_take_address": "Пожалуйста, укажите адрес доставки:",
    "about_us_text": "Кафе 'The Kitchen' ☕️\nМы рады предложить вам вкуснейший кофе и свежую выпечку!\n\n📍 *Наш адрес:* [Сюда ваш точный адрес]\n📞 *Телефон:* [Сюда ваш контактный телефон]\n🕒 *Часы работы:* Пожалуйста, смотрите актуальное расписание через кнопку 'Статус и Расписание' в главном меню.\n\nЖдем вас в гости и принимаем заказы через этого бота!",
    "payment_details": "Пожалуйста, произведите оплату на следующие реквизиты:\n[Сюда ваши реквизиты для оплаты: номер карты, название банка, имя получателя и т.д.]\nСумма к оплате: *{total_price_formatted}*\n\nПосле оплаты, пожалуйста, прикрепите фото или скриншот чека в ответ на это сообщение.",
    "ask_for_review": "Благодарим за ваш заказ! 😊 Пожалуйста, оставьте ваш отзыв или поставьте оценку от 1 до 5. Ваше мнение очень важно для нас!",
    "thanks_for_review": "Спасибо большое за ваш отзыв! Мы ценим ваше мнение и постараемся стать еще лучше. ✨",
    "order_delivery_confirmed_ask_review": "Спасибо за подтверждение! 😊 Будем очень благодарны, если вы оставите отзыв о вашем заказе.",
    "order_received_notification": "📦 Заказ получен! Спасибо, что сообщили.",
    "feedback_prompt_name": "Пожалуйста, введите ваше имя (как к вам обращаться):",
    "feedback_prompt_phone": "Пожалуйста, введите ваш контактный телефон (для обратной связи, если потребуется):",
    "feedback_prompt_message": "Напишите ваше сообщение/отзыв/предложение:",
    "feedback_thanks": "Спасибо за вашу обратную связь! Мы ее изучим.",
    "feedback_admin_notification_format": (
        "Feedback Received:\n"
        "Telegram User: {telegram_user_name} (ID: `{telegram_user_id}`)\n"
        "Provided Name: {feedback_name}\n"
        "Provided Phone: {feedback_phone}\n\n"
        "Message:\n{feedback_message}"
    )
}

print("Конфигурация загружена (config.py)")
