import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from logic import StoreManager, DATABASE
from datetime import datetime
import os

welcome_text = (
    "Добро пожаловать в бот потерянных вещей Международной школы Астана (МША)!\n\n"
    "Этот бот создан, чтобы помогать студентам, учителям и сотрудникам школы находить потерянные вещи. Если вы потеряли что-то или нашли чужую вещь, используйте функционал бота:\n\n"
    "- Поиск потерянных вещей — просматривайте список найденных вещей.\n"
    "- Добавление новой записи (для кураторов)* — добавьте информацию о найденной вещи.\n"
    "- Удаление записей (для кураторов)* — удаляйте устаревшие или некорректные записи.\n\n"
    "Надеемся, что этот сервис сделает вашу школьную жизнь проще и удобнее! 😊")

AUTHORIZED_USER_IDS = [123456789, 1210665620]
TELEGRAM_TOKEN = '6712865092:AAHubde1HD3RkAM-DeP32DR-V4aEL1onSQ4'
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def gen_markup(user_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Регистрация потеряшки", callback_data="reg_lost"),
        InlineKeyboardButton("Просмотр потеряшек", callback_data="see_lost")
    )
    if user_id in AUTHORIZED_USER_IDS:
        markup.add(InlineKeyboardButton("Удалить потеряшку", callback_data="delete_lost"))
    return markup

def gen_getitem(items):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    for item in items:
        markup.add(InlineKeyboardButton(item[1], callback_data=f"item_{item[0]}"))
    return markup

def date_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    markup.add(
        InlineKeyboardButton("3 дня", callback_data="last3"),
        InlineKeyboardButton("неделя", callback_data="lastweek"),
        InlineKeyboardButton("За всё время", callback_data="alltime")
    )
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "reg_lost":
        if call.from_user.id in AUTHORIZED_USER_IDS:
            bot.send_message(call.message.chat.id, "Введите название вещи:")
            bot.register_next_step_handler(call.message, reg_step1)
        else:
            bot.send_message(call.message.chat.id, "У вас нет прав для добавления потеряшек.")
    
    elif call.data == "see_lost":
        res = manager.get_items()
        if not res:
            bot.send_message(call.message.chat.id, "Недостаточно потеряшек для отображения.")
            return
        markup = create_page_markup(0)
        img, s = page_creator(res, 0)
        bot.send_photo(call.message.chat.id, img)
        bot.send_message(call.message.chat.id, s, reply_markup=markup)

    elif call.data.startswith("item"):
        item_id = call.data.split("_")[1]
        item_info = manager.get_items_data(item_id)
        if item_info:
            bot.send_message(call.message.chat.id, f"{item_info[1]}\n")
            img_path = item_info[3]
            if os.path.exists(img_path):
                with open(img_path, 'rb') as img:
                    bot.send_photo(call.message.chat.id, img)
            else:
                bot.send_message(call.message.chat.id, "Изображение не найдено.")
        else:
            bot.send_message(call.message.chat.id, "Информация о предмете не найдена.")

    elif call.data == "delete_lost":
        if call.from_user.id in AUTHORIZED_USER_IDS:
            bot.send_message(call.message.chat.id, "Введите ID вещи для удаления:")
            bot.register_next_step_handler(call.message, delete_step)
        else:
            bot.send_message(call.message.chat.id, "У вас нет прав для удаления потеряшек.")

    elif call.data.startswith("delete"):
        item_id = call.data.split("_")[1]
        if call.from_user.id in AUTHORIZED_USER_IDS:
            manager.delete_item(item_id)
            bot.send_message(call.message.chat.id, "Вещь удалена из списка потеряшек.")
        else:
            bot.send_message(call.message.chat.id, "У вас нет прав для удаления потеряшек.")

    elif call.data.startswith("page_back") or call.data.startswith("page_forward"):
        res = manager.get_items()
        if not res:
            bot.send_message(call.message.chat.id, "Недостаточно потеряшек для отображения.")
            return
        
        item_id = int(call.data.split("_")[2])
        message_id = call.message.id
        
        if item_id >= 1 and call.data.startswith("page_back"):
            item_id -= 1
        elif (item_id + 1) * 4 < len(res) and call.data.startswith("page_forward"):
            item_id += 1
        else:
            return
        
        img, s = page_creator(res, item_id)
        markup = create_page_markup(item_id)
        bot.edit_message_text(text=s, chat_id=call.message.chat.id, message_id=message_id, reply_markup=markup)
        bot.edit_message_media(media=telebot.types.InputMedia(type='photo', media=img), chat_id=call.message.chat.id, message_id=message_id-1)

def create_page_markup(i):
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    markup.add(
        InlineKeyboardButton("Назад", callback_data=f"page_back_{i}"),
        InlineKeyboardButton(f"Страница {i + 1}", callback_data="1"),
        InlineKeyboardButton("Вперёд", callback_data=f"page_forward_{i}")
    )
    return markup

def reg_step1(message):
    name = message.text
    bot.send_message(message.chat.id, "Отправьте фото вещи:")
    bot.register_next_step_handler(message, photo, name=name)

def page_creator(res, i):
    s = ""
    paths = []
    last = (i + 1) * 4
    if len(res) < last:
        last = len(res)
    for item in res[i * 4:last]:
        paths.append(item[3])
        s += f"{item[0]}. {item[1]}\n{item[2]}\n\n"
    manager.collage_creation(paths, "output.png")
    img = open("output.png", 'rb')
    return img, s

def photo(message, name):
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    
    
    if not os.path.exists('img'):
        os.makedirs('img')

    with open(f"img/{message.id}.jpg", 'wb') as new_file:
        new_file.write(downloaded_file)

    rightnow = datetime.now()
    manager.add_items(name, f"img/{message.id}.jpg", rightnow)
    bot.send_message(message.chat.id, "Вещь добавлена в список потеряшек")

def delete_step(message):
    try:
        item_id = int(message.text)
        manager.delete_item(item_id)
        bot.send_message(message.chat.id, "Вещь удалена из списка потеряшек.")
    except ValueError:
        bot.send_message(message.chat.id, "Неправильный ID. Пожалуйста, введите правильный ID.")

@bot.message_handler(commands=['start'])
def message_handler(message):
    bot.send_message(message.chat.id, welcome_text, reply_markup=gen_markup(message.from_user.id))

if __name__ == "__main__":
    manager = StoreManager(DATABASE)
    bot.infinity_polling()
