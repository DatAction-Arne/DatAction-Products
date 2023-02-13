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

if (any(df['product-name'].isin(['Honeywell Thor CV31']))):
    print(df[df['product-name'] == 'Honeywell Thor CV31'].index)
    print(len(df.index))
    df = df.drop(df[df['product-name'] == 'Honeywell Thor CV31'].index)
    print(len(df.index))















###
