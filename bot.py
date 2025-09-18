import qrcode
import telebot
from io import BytesIO
import json
import datetime
import os
# ВНИМАНИЕ ЗАМЕНИТЕ ТГ АЙДИ АДМИНА С МОЕГО НА СВОЙ ЧТО Я У ВАС БЫЛ ДОСТУП К КОМАНДЕ /users
TOKEN = 'сюда свой токен бота'
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 6820237306

users_data = {}

try:
    with open('users_data.json', 'r', encoding='utf-8') as f:
        users_data = json.load(f)
except:
    pass

def save_users_data():
    with open('users_data.json', 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

def get_russian_date():
    months = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    now = datetime.datetime.now()
    return f"{now.day} {months[now.month]} {now.year} год"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    if user_id not in users_data:
        users_data[user_id] = {
            'first_name': message.from_user.first_name or '',
            'last_name': message.from_user.last_name or '',
            'username': message.from_user.username or '',
            'join_date': get_russian_date(),
            'links': []
        }
        save_users_data()
    
    welcome_text = "🤖 Привет! Я бот для генерации QR-кодов\n\n📎 Просто отправь мне любую ссылку, и я создам QR-код\n\n🔗 Пример: https://example.com"
    bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = "📋 Как пользоваться ботом:\n\n1. Отправь мне любую ссылку\n2. Я создам QR-код для этой ссылки\n3. Скачай QR-код и используй где угодно"
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['users'])
def send_users_file(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нет доступа")
        return
    
    now = datetime.datetime.now()
    filename = f"users_{now.day}.{now.month}.{now.year}.txt"
    
    with open(filename, 'w', encoding='utf-8-sig') as f:
        for user_id, user_data in users_data.items():
            first_name = user_data.get('first_name', '') or 'Не указано'
            last_name = user_data.get('last_name', '') or ''
            username = user_data.get('username', '') or 'Не указан'
            join_date = user_data.get('join_date', '') or 'Не указана'
            links = user_data.get('links', [])
            
            full_name = f"{first_name} {last_name}".strip()
            if not full_name:
                full_name = "Не указано"
                
            f.write(f"ник ({full_name}) : @{username}\n")
            f.write(f"дата первого входа : {join_date}\n")
            f.write("все ссылки \n")
            f.write("{ тут это скобочки\n")
            for link in links:
                f.write(f"{link}\n")
            f.write("тут отображаются\n")
            f.write("}\n\n")
    
    with open(filename, 'rb') as f:
        bot.send_document(message.chat.id, f, caption="📊 Файл с пользователями")
    
    os.remove(filename)

def is_url(text):
    return text.startswith(('http://', 'https://', 'www.'))

def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()
    user_id = str(message.from_user.id)
    
    if user_id not in users_data:
        users_data[user_id] = {
            'first_name': message.from_user.first_name or '',
            'last_name': message.from_user.last_name or '',
            'username': message.from_user.username or '',
            'join_date': get_russian_date(),
            'links': []
        }
    
    if is_url(text):
        try:
            if not text.startswith(('http://', 'https://')):
                text = 'https://' + text
            
            users_data[user_id]['links'].append(text)
            save_users_data()
            
            bot.send_message(message.chat.id, "🔄 Создаю QR-код...")
            qr_image = generate_qr_code(text)
            
            bot.send_photo(message.chat.id, qr_image, caption=f"✅ QR-код для ссылки:\n{text}")
            
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Ошибка при создании QR-кода")
            
    else:
        if not text.startswith('/'):
            bot.send_message(message.chat.id, "❌ Это не похоже на ссылку. Отправь мне валидный URL")

if __name__ == '__main__':
    bot.polling(none_stop=True)
