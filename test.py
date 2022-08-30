import numpy as np
import pandas as pd
import json
import re
from sqlalchemy import create_engine
from datetime import datetime, date
from pytz import timezone

f = open('products.json')
products = json.load(f)
#
# products.pop('accessories')
#
df = pd.DataFrame(products)

dfSub = df[df['product-group'] == 'printers']

#print(dfSub['product-name'], dfSub['SPEED'])

today = datetime.today()
someday = datetime.strptime('20-6-2022', '%d-%m-%Y')

diff = someday - today

print(diff.days)

print((datetime.today().strftime('%d-%m-%Y')))















###
