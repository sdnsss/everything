import json
import time
import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()
token = os.getenv("API_TOKEN")
url = os.getenv("API_URL")


def find_difference(file1, file2):
    with open(file1, "r") as f1, open(file2, "r") as f2:
        data1 = {item["sku"]: item for item in json.load(f1)}
        data2 = {item["sku"]: item for item in json.load(f2)}

        result = []
        for item1 in data1.values():
            item2 = data2.get(item1["sku"])

            if item2:
                diff = int(item1["quantity"]) - int(item2["quantity"])
                if diff > 2:
                    print("yay")
                    result.append({
                        "id": item2["id"],
                        "sku": item2["sku"],
                        "difference": diff,
                        "new_quantity": item2["quantity"]
                    })
        return result


def create_session():
    s = requests.Session()
    s.headers.update({
        'Authorization': 'Bearer ' + token
    })

    def api_calls(r, *args, **kwargs):
        calls_left = r.headers['X-Ratelimit-Remaining']
        if int(calls_left) == 1:
            print("limit close turning off")
            time.sleep(5)

    s.hooks["response"] = api_calls

    return s


def one_loader():
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    sess = create_session()
    respstock = sess.get(url + "/productsstock.json")
    respsvar = sess.get(url + "/productsvariationsstock.json")
    base_stock_json = respstock.json()
    variable_stock_json = respsvar.json()

    for product in variable_stock_json:
        product['quantity'] = product['stocks'][0]['quantity']
        del product['stocks']
    with open(f"{year}-{month}-{day}-var", 'w') as f:
        json.dump(variable_stock_json, f)

    for product in base_stock_json:
        product['quantity'] = product['stocks'][0]['quantity']
        del product['stocks']
    with open(f"{year}-{month}-{day}", 'w') as f:
        json.dump(base_stock_json, f)


def loader():
    current_time = datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    sess = create_session()
    respstock = sess.get(url + "/productsstock.json")
    respsvar = sess.get(url + "/productsvariationsstock.json")
    base_stock_json = respstock.json()
    variable_stock_json = respsvar.json()

    for product in variable_stock_json:
        product['quantity'] = product['stocks'][0]['quantity']
        del product['stocks']
    with open(f"{year}-{month}-{day}-var", 'w') as f:
        json.dump(variable_stock_json, f)

    for product in base_stock_json:
        product['quantity'] = product['stocks'][0]['quantity']
        del product['stocks']
    with open(f"{year}-{month}-{day}", 'w') as f:
        json.dump(base_stock_json, f)

    time_min = current_time - timedelta(days=1)
    day_min = time_min.day
    year_min = time_min.year
    month_min = time_min.month

    popular_data = find_difference(f"{year_min}-{month_min}-{day_min}", f"{year}-{month}-{day}")
    popular_data_var = find_difference(f"{year_min}-{month_min}-{day_min}-var", f"{year}-{month}-{day}-var")

    print("popular data")
    print(popular_data)
    print("var popular")
    print(popular_data_var)

    for item in popular_data_var:
        popular_data.append(item)

    with open(f'{year}-{month}-{day}-popular', 'w') as f:
        json.dump(popular_data, f)


def main():
    scheduler = BackgroundScheduler()
    scheduler.add_job(loader, 'cron', day='*/1', hour=12, minute='00')
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
