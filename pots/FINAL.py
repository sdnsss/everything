import pandas as pd
import requests
import csv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import schedule
import time
import base64
import os

os.chdir("/root/pots")

# Указываем данные для аутентификации
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('/root/pots/credentials.json', scope)
client = gspread.authorize(creds)

# Открываем Google Таблицу по ее ID
spreadsheet_id = '1tUYsqbU736Ub5htcrS1UoBiFnj823P1a511LpgDX_zk'
sheet = client.open_by_key(spreadsheet_id).sheet1
# Получаем список всех значений в таблице
all_values = sheet.get_all_values()

# Замените на ваш токен бота
TOKEN = "6885449447:AAECgoyV5n2rrEvJ4UBuB2dm8hNF5uQeinc"

def get_access_token():
    # Ваши учетные данные
    username = "alexashka.zp@gmail.com"
    password = "Barcelona93"

    # Кодируем пароль в формат base64
    encoded_password = base64.b64encode(password.encode()).decode()

    # URL для запроса на аутентификацию
    url = "https://api-seller.rozetka.com.ua/sites"

    # Параметры запроса
    data = {
        "username": username,
        "password": encoded_password
    }

    # Отправляем POST-запрос для аутентификации
    response = requests.post(url, json=data)

    # Проверяем статус код ответа
    if response.status_code == 200:
        # Получаем JSON-ответ
        response_json = response.json()
        # Извлекаем токен доступа из ответа
        access_token = response_json['content']['access_token']

        # Выводим токен доступа
        print("Access Token:", access_token)
        return access_token
    else:
        print("Ошибка аутентификации:", response.text)
        return None

# Расписание для обновления токена каждые 24 часа в 22:00
schedule.every().day.at("22:00").do(get_access_token)

# Обработчик команды /start
def start(update, context):
    update.message.reply_text("Я киберраб, который делает работу за кожанных, дай мне код заказа")

# Обработчик текстового сообщения
def echo(update, context):
    order_id = update.message.text.strip()
    try:
        # Получаем информацию о заказе
        order_info = get_order_info(order_id)
        update.message.reply_text(order_info)

    except Exception as e:
        update.message.reply_text(f"Ошибка: {e}")

# Функция для получения информации о заказе
def get_order_info(order_id):
    # Получаем токен доступа
    token_roz = get_access_token()

    # Указываем язык ответа
    language = "ru"

    # Формируем URL запроса
    url = f"https://api-seller.rozetka.com.ua/orders/{order_id}"

    # Заголовки запроса
    headers = {
        "Authorization": f"Bearer {token_roz}",
        "Content-Language": language
    }

    # Отправляем GET-запрос к API
    response = requests.get(url, headers=headers)

    # Проверяем статус код ответа
    if response.status_code == 200:
        order_data = response.json()
        order_id = order_data['content']['id']
        created_date = order_data['content']['created']
        items = order_data['content']['items_photos']
        order_info_str = f"ID заказа: {order_id}, Дата создания: {created_date}\n"

        df = pd.read_csv('tovar-cod.csv', delimiter=';', header=None)
        tovar_cod_dict = df.set_index(df.columns[0]).to_dict()[df.columns[1]]

        for item in items:
            item_id = item['id']
            item_name = item['item_name']
            item_price = item['item_price']
            product_id = item_id
            url = "https://api-seller.rozetka.com.ua/items/search"
            params = {
                "product_id": product_id
            }
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                product_data = response.json()
                price_offer_id = product_data['content']['items'][0]['price_offer_id']

                if price_offer_id.startswith('um-'):
                    # Удаляем 'um-' из начала строки
                    price_offer_id = price_offer_id[3:]
                    # Добавляем приписку "unmall"
                    price_offer_id
                    # Проверяем длину строки 'price_offer_id'
                    if len(price_offer_id) < 13:
                        # Вычисляем количество нулей, которое нужно добавить
                        zeros_to_add = 13 - len(price_offer_id)
                        # Добавляем нули в начало строки
                        code = price_offer_id.zfill(13)
                        # Выводим значение 'price_offer_id'
                        print("Price Offer ID-Unmall:", price_offer_id)
                        order_info_str += f"ID товара: {item_id}, Название: {item_name}, Цена: {item_price}, Код товара: {code}\n"
                    else:
                        print("Price Offer ID-Unmall:", price_offer_id)
                        code=price_offer_id
                        order_info_str += f"ID товара: {item_id}, Название: {item_name}, Цена: {item_price}, Код товара: {code}\n"

                if price_offer_id.startswith('11'):
                    price_offer_id = int(price_offer_id)
                    with open('tovar-cod.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=';')
                        for row in reader:
                            if int(row[0]) == price_offer_id:
                                code = row[1][3:]
                                order_info_str += f"ID товара: {item_id}, Название: {item_name}, Цена: {item_price}, Код товара: {code}\n"
                                break
                        else:
                            order_info_str += f"ID товара: {item_id}, Название: {item_name}, Цена: {item_price}, Код товара не найден\n"
            else:
                order_info_str += f"ID товара: {item_id}, Название: {item_name}, Цена: {item_price}, Ошибка при получении информации о товаре\n"
        # Ищем первую строку, где первые пять столбцов пустые
        for i, row in enumerate(all_values):
            if all(cell == '' for cell in row[:7]):
                next_available_row = i + 1
                break
        else:
            next_available_row = len(all_values) + 1

        # Данные для записи
        data_to_write = [
            created_date,  # Дата
            order_id,  # Номер розетки
            code,  # Номер BB/UM
            item_name,
            item_price
        ]

        # Записываем данные в Google Таблицу
        sheet.append_row(data_to_write)
        return order_info_str
    else:
        raise Exception(f"Ошибка при выполнении запроса: {response.text}")

def main():
    # Создаем объект бота и регистрируем обработчики
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Запускаем бота
    updater.start_polling()

    # Запускаем планировщик задач
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
