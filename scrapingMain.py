import requests
import json
import numpy as np
import pandas as pd
import schedule
import time
from datetime import datetime
from pytz import timezone
from utils import *
from scrapingJT import *
from scrapingPM import *

def job():
    today = datetime.today()
    print("Scraping started at {}..........".format(datetime.now(timezone('Europe/Brussels')).strftime('%H:%M:%S %d-%m-%Y')))
    with open('products.json', 'r') as f:
        products = json.load(f)

    productsJT = scrapingJT(products)
    products = productsJT
    productsPM = scrapingPM(products)
    products = productsPM

    products = pd.DataFrame(products)
    diff = [(today - datetime.strptime(prod, '%d-%m-%Y')).days for prod in products['release-date']]
    isNew = [True if el < 90 else False for el in diff]
    products['new'] = isNew

    with open('products.json', 'w') as f:
        json.dump(products.to_dict(), f)


schedule.every().second.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
