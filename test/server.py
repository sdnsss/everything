import glob
import json
import os
import telebot
from datetime import datetime, timedelta
import re
import pandas as pd
from telebot.types import InputFile

BOT_TOKEN = os.getenv('BOT_TOKEN')


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def find_difference(file1, file2):
    with open(file1, "r") as f1, open(file2, "r") as f2:
        data1 = {item["sku"]: item for item in json.load(f1)}
        data2 = {item["sku"]: item for item in json.load(f2)}

        result = []
        for item1 in data1.values():
            item2 = data2.get(item1["sku"])
            if item2 is not None:
                diff = int(item1["difference"]) + (int(item1["new_quantity"]) - int(item2["new_quantity"]))
                result.append({
                    "id": item2["id"],
                    "sku": item2["sku"],
                    "difference": diff,
                    "new_quantity": item2["new_quantity"]
                })
            else:
                result.append(item1)

        for item2 in data2.values():
            item1 = data1.get(item2["sku"])
            if item1 is None:
                result.append(item2)

        return result


def find_sum(file1, file2):
    with open(file2, "r") as f2:
        data2 = {item["sku"]: item for item in json.load(f2)}

        result = []
        for item1 in file1:
            item2 = data2.get(item1["sku"])

            if item2 is not None:
                diff = int(item1["difference"]) + (int(item1["new_quantity"]) - int(item2["new_quantity"]))
                result.append({
                    "id": item2["id"],
                    "sku": item2["sku"],
                    "difference": diff,
                    "new_quantity": item2["new_quantity"]
                })
            else:
                result.append(item1)

        data1 = {item["sku"]: item for item in file1}

        for item2 in data2.values():
            item1 = data1.get(item2["sku"])

            if item1 is None:
                result.append(item2)

        return result


bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['test'])
def send_test(message):
    print(message.text)
    bot.send_message(message.chat.id, "Everything is great!", parse_mode="Markdown")


@bot.message_handler(commands=['check'])
def send_test(message):
    print(message.text)
    text = glob.glob("*-popular")
    text.sort(key=natural_keys)
    for item in text:
        bot.send_message(message.chat.id, item, parse_mode="Markdown")

@bot.message_handler(commands=['excel'])
def send_excel(message):
    first_date = message.text.split(" ")[1]
    second_date = message.text.split(" ")[2]

    first_year = first_date.split("-")[0]
    first_month = first_date.split("-")[1]
    first_day = first_date.split("-")[2]

    second_year = second_date.split("-")[0]
    second_month = second_date.split("-")[1]
    second_day = second_date.split("-")[2]

    start_date = datetime.strptime(f"{first_year}-{first_month}-{first_day}", '%Y-%m-%d')
    end_date = datetime.strptime(f"{second_year}-{second_month}-{second_day}", '%Y-%m-%d')

    time_pl = start_date + timedelta(days=1)
    year_pl = time_pl.year
    month_pl = time_pl.month
    day_pl = time_pl.day

    request = find_difference(f"{first_year}-{first_month}-{first_day}-popular",
                              f"{year_pl}-{month_pl}-{day_pl}-popular")


    request1 = None

    if time_pl == end_date:
        request1 = sorted(request, key=lambda d: d["difference"], reverse=True)

    while time_pl != end_date:
        time_pl = time_pl + timedelta(days=1)
        year_pl_2 = time_pl.year
        month_pl_2 = time_pl.month
        day_pl_2 = time_pl.day
        try:
            tmp = find_sum(request, f"{year_pl_2}-{month_pl_2}-{day_pl_2}-popular")

            request = tmp

            request1 = sorted(request, key=lambda d: d['difference'], reverse=True)

        except:
            print("Small error with data")

    i = 0
    data = {
        'sku': [],
        'quantity': [],
        'difference': []
    }
    for item in request1:
        if i != 3000:
            data['sku'].append(item['sku'])
            data['quantity'].append(item['new_quantity'])
            data['difference'].append(item['difference'])

            i += 1
        else:
            break
    df = pd.DataFrame(data)
    df.to_excel(f'./{start_date}&{end_date}.xlsx', index=False)
    bot.send_document(message.chat.id, InputFile(f'./{start_date}&{end_date}.xlsx'))

@bot.message_handler(commands=['diff'])
def send_difference(message):
    first_date = message.text.split(" ")[1]
    second_date = message.text.split(" ")[2]

    first_year = first_date.split("-")[0]
    first_month = first_date.split("-")[1]
    first_day = first_date.split("-")[2]

    second_year = second_date.split("-")[0]
    second_month = second_date.split("-")[1]
    second_day = second_date.split("-")[2]

    start_date = datetime.strptime(f"{first_year}-{first_month}-{first_day}", '%Y-%m-%d')
    end_date = datetime.strptime(f"{second_year}-{second_month}-{second_day}", '%Y-%m-%d')

    time_pl = start_date + timedelta(days=1)
    year_pl = time_pl.year
    month_pl = time_pl.month
    day_pl = time_pl.day

    request = find_difference(f"{first_year}-{first_month}-{first_day}-popular",
                              f"{year_pl}-{month_pl}-{day_pl}-popular")


    request1 = None

    if time_pl == end_date:
        request1 = sorted(request, key=lambda d: d["difference"], reverse=True)

    while time_pl != end_date:
        time_pl = time_pl + timedelta(days=1)
        year_pl_2 = time_pl.year
        month_pl_2 = time_pl.month
        day_pl_2 = time_pl.day

        tmp = find_sum(request, f"{year_pl_2}-{month_pl_2}-{day_pl_2}-popular")

        request = tmp

        request1 = sorted(request, key=lambda d: d['difference'], reverse=True)

    i = 0
    for item in request1:
        if i != 100:
            text = "! Sku = " + item["sku"] + " ! Difference = " + str(item["difference"]) + " ! New quantity = " + str(
                item["new_quantity"])
            print(text)
            bot.send_message(message.chat.id, text, parse_mode="Markdown")
            i += 1
        else:
            break


bot.infinity_polling()

"""
                

"""
