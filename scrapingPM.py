import requests
import json
import re
import html5lib
import numpy as np
import pandas as pd
import itertools
import io
import urllib.request
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from itertools import chain
from PIL import Image
from utils import *
from time import sleep
from datetime import datetime
from pytz import timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def scrapingPM(products):
    if products is None:
        dfProduct = pd.DataFrame(columns=['release-date', 'supplier', 'product-group', 'product-name', 'product-name-type-only', 'image', 'link', 'accessories',
                                          'SCANNING', 'WIFI', 'WWAN', 'GPS', 'RESOLUTION', 'BLUETOOTH', 'NFC', 'OTHER', 'FREEZER MODEL', 'RFID', 'OS', 'KEYPAD', 'MEMORY', 'CAMERA', 'IP RATING',
                                          'BATTERY', 'SCAN RATE', 'SYSTEM INTERFACE', 'MEDIA WIDTH', 'SPEED', 'PRINT MODE', 'PRINT WIDTH'])
    else:
        dfProduct = pd.DataFrame.from_dict(products)

    baseURL = 'https://www.pointmobile.com'

    imgDict = {}
    counter = 0
    supplier = 'Point Mobile'
    buttonNames = ['product-PRODUCTS01', 'product-PRODUCTS02', 'product-PRODUCTS03', 'product-PRODUCTS04', 'product-PRODUCTS06']

    #### Find all product group urls ####
    request = requests.get(urljoin(baseURL, '/en/products-all'), timeout=10)


    options = Options()
    options.add_argument('--headless')
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("window-size=1920x1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options = options)
    driver.get(baseURL + '/en/products-all')

    for button in buttonNames[0:]:
        driver.get(baseURL + '/en/products-all')
        btn = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, button)))
        btn.click()
        sleep(3)

        parsed = BeautifulSoup(driver.page_source, 'html5lib')
        listKeep = ['mobile computers', 'rugged smartphone', 'handheld terminal', 'rfid solution', 'bluetooth scanner']
        hrefProductList = [item['href'] for item in parsed.find_all('a', {'class': ['link--more_information', 'link--more_information__plus'] })]
        nameProductList = [item.text for item in parsed.find_all('p', {'class': ['text--product_name'] })]

        #print('Product url: {} \n'.format(hrefProductList))
        #print('Product names: {} \n'.format(nameProductList))

        #### Sub groups in product groups ####
        for urlProduct, nameProduct in zip(hrefProductList[0:], nameProductList[0:]):
            dictSpecs = {}
            dictProduct = {}

            # Check if product name in dataframe
            if not dfProduct[dfProduct['product-name'] == (supplier + ' ' +  nameProduct.replace('/','-'))].empty:
                print('{} Already in dataframe'.format(supplier + ' ' +  nameProduct.replace('/','-')))
                #continue
            else:
                dictProduct['release-date'] = datetime.today().strftime('%d-%m-%Y')

            request = requests.get(baseURL + urlProduct)
            parsed = BeautifulSoup(request.content, 'html5lib')

            attrList = [item.text for item in parsed.find_all("div", {'class' : 'text--title' }) ]
            contentList = [item.get_text(separator=", ", strip=True).strip() for item in parsed.find_all("div", {'class' : 'text--description' }) ]


            # Specs
            # Keypad
            textAll = parsed.text
            if 'numeric' in textAll.lower().replace("alpha numeric", '').replace("function numeric", ''):
                if 'KEYPAD' in dictSpecs and 'numeric' not in dictSpecs['KEYPAD']: dictSpecs['KEYPAD'].append('numeric')
                elif 'KEYPAD' not in dictSpecs: dictSpecs['KEYPAD'] = ['numeric']
            if 'alpha numeric' in textAll.lower():
                if 'KEYPAD' in dictSpecs and 'alpha numeric' not in dictSpecs['KEYPAD']: dictSpecs['KEYPAD'].append('alpha numeric')
                elif 'KEYPAD' not in dictSpecs: dictSpecs['KEYPAD'] = ['alpha numeric']
            if 'function numeric' in textAll.lower():
                if 'KEYPAD' in dictSpecs and 'function numeric' not in dictSpecs['KEYPAD']: dictSpecs['KEYPAD'].append('function numeric')
                elif 'KEYPAD' not in dictSpecs: dictSpecs['KEYPAD'] = ['function numeric']

            # Other
            if 'handstrap' in textAll.lower().replace('-', '').replace(' ', ''):
                if 'OTHER' in dictSpecs and 'hand-strap' not in dictSpecs['OTHER']: dictSpecs['OTHER'].append('hand-strap')
                elif 'OTHER' not in dictSpecs: dictSpecs['OTHER'] = ['hand-strap']
            if 'pistolgrip' in textAll.lower().lower().replace('-', '').replace(' ', ''):
                if 'OTHER' in dictSpecs and 'pistol grip' not in dictSpecs['OTHER']: dictSpecs['OTHER'].append('pistol grip')
                elif 'OTHER' not in dictSpecs: dictSpecs['OTHER'] = ['pistol grip']
            if 'hotswap' in textAll.lower().lower().replace('-', '').replace(' ', ''):
                if 'OTHER' in dictSpecs and 'hot-swap' not in dictSpecs['OTHER']: dictSpecs['OTHER'].append('hot-swap')
                elif 'OTHER' not in dictSpecs: dictSpecs['OTHER'] = ['hot-swap']

            # Interfaces
            if 'usb' in textAll.lower():
                if 'SYSTEM INTERFACE' in dictSpecs and 'USB' not in dictSpecs['SYSTEM INTERFACE']: dictSpecs['SYSTEM INTERFACE'].append('USB')
                elif 'SYSTEM INTERFACE' not in dictSpecs: dictSpecs['SYSTEM INTERFACE'] = ['USB']
            if 'kbw' in textAll.lower():
                if 'SYSTEM INTERFACE' in dictSpecs and 'Keyboard Wedge' not in dictSpecs['SYSTEM INTERFACE']: dictSpecs['SYSTEM INTERFACE'].append('Keyboard Wedge')
                elif 'SYSTEM INTERFACE' not in dictSpecs: dictSpecs['SYSTEM INTERFACE'] = ['Keyboard Wedge']

            for attr, spec in zip(attrList, contentList):
                # WIFI
                if 'wi-fi' in spec.lower() or 'wlan' in spec.lower():
                    dictSpecs['WIFI'] = ['Supported']

                # WWAN
                if ('4g' in spec.lower() and not '4gb' in spec.lower()) or 'sim' in spec.lower() or 'esim' in spec.lower() or 'wwan' in spec.lower():
                    dictSpecs['WWAN'] = ['Supported']

                # NFC
                if 'nfc' in spec.lower() or 'nfc' in attr.lower():
                    dictSpecs['NFC'] = ['Supported']

                # GPS
                if 'gps' in spec.lower():
                    dictSpecs['GPS'] = ['Supported']

                # FREEZER UNIT
                if 'freezer' in spec.lower() or 'cold storage' in spec.lower():
                    dictSpecs['FREEZER MODEL'] = ['Supported']

                # Bluetooth
                if 'bt' in spec.lower() or 'bluetooth' in spec.lower() or 'ble' in spec.lower():
                    dictSpecs['BLUETOOTH'] = ['Supported']

                # RFID
                if 'rfid' in spec.lower() or 'rfid' in attr.lower():
                    dictSpecs['RFID'] = ['Supported']

                # Scanning
                if ('2d barcode' in spec.lower() or '2d imager' in spec.lower()):
                    if 'SCANNING' in dictSpecs and '2D standard range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('2D standard range imager')
                    elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['2D standard range imager']
                if ('1d/2d barcode' in spec.lower() or '1d/2d imager' in spec.lower() or '1d/2d led barcode' in spec.lower()):
                    if 'SCANNING' in dictSpecs and '2D standard range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('2D standard range imager')
                    elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['2D standard range imager']
                if ('1d/2d standard' in spec.lower() or '2d standard' in spec.lower()):
                    if 'SCANNING' in dictSpecs and '2D standard range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('2D standard range imager')
                    elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['2D standard range imager']
                if ('2d long' in spec.lower() or '1d/2d long' in spec.lower() or '2d extra-long' in spec.lower()):
                    if 'SCANNING' in dictSpecs and '2D extended range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('2D extended range imager')
                    elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['2D extended range imager']
                if ('2d mid' in spec.lower() or '1d/2d mid' in spec.lower()):
                    if 'SCANNING' in dictSpecs and '2D medium range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('2D medium range imager')
                    elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['2D medium range imager']
                if ('1d barcode' in spec.lower() or '1d laser' in spec.lower() or '1d standard' in spec.lower()):
                    if 'SCANNING' in dictSpecs and '1D standard range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('1D standard range imager')
                    elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['1D standard range imager']
                if ('1d extra-long' in spec.lower()):
                    if 'SCANNING' in dictSpecs and '1D extended range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('1D extended range imager')
                    elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['1D extended range imager']
                if 'dpm' in spec.lower():
                    if 'SCANNING' in dictSpecs and 'DPM Support' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('DPM Support')
                    elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['DPM Support']
                if 'digimarc' in spec.lower():
                    if 'SCANNING' in dictSpecs and 'Digimarc Support' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('Digimarc Support')
                    elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['Digimarc Support']


                # OS
                if 'os' in attr.lower():
                    specList = spec.replace('Upgradeable', '').split(', ')
                    for el in specList:
                        if ('android' in el.lower()) and ('or' not in el.lower()):
                            try:
                                content = 'Android ' + el.split(' ')[1]
                            except:
                                content = 'Android'
                            if 'OS' in dictSpecs and (content) not in dictSpecs['OS']: dictSpecs['OS'].append(content)
                            elif 'OS' not in dictSpecs: dictSpecs['OS'] = [content]
                        elif ('android' in el.lower()) and ('or' in el.lower()):
                            if 'OS' in dictSpecs and (el) not in dictSpecs['OS']: dictSpecs['OS'].append(el)
                            elif 'OS' not in dictSpecs: dictSpecs['OS'] = [el]
                        elif ('windows' in el.lower()):
                            if 'OS' in dictSpecs and (el) not in dictSpecs['OS']: dictSpecs['OS'].append(el)
                            elif 'OS' not in dictSpecs: dictSpecs['OS'] = [el]
                        elif ('ios' in el.lower()):
                            if 'OS' in dictSpecs and (el) not in dictSpecs['OS']: dictSpecs['OS'].append(el)
                            elif 'OS' not in dictSpecs: dictSpecs['OS'] = [el]

                # Memory
                if attr.lower() == 'memory and storage':
                    specList = spec.split(', ')
                    for el in specList:
                        match = re.findall('\d{1,3}.B\/\d{1,3}.B', spec.replace('RAM', '').replace('ROM', '').replace(' ', ''))
                        if match:
                            for m in match:
                                if 'MEMORY' in dictSpecs and (m.split('/')[0] + ' RAM, ' + m.split('/')[1] + ' ROM') not in dictSpecs['MEMORY']: dictSpecs['MEMORY'].append((m.split('/')[0] + ' RAM, ' + m.split('/')[1] + ' ROM'))
                                elif 'MEMORY' not in dictSpecs: dictSpecs['MEMORY'] = [(m.split('/')[0] + ' RAM, ' + m.split('/')[1] + ' ROM')]
                        elif 'ram' in el.lower():
                            if 'MEMORY' in dictSpecs and (el) not in dictSpecs['MEMORY']: dictSpecs['MEMORY'].append(el)
                            elif 'MEMORY' not in dictSpecs: dictSpecs['MEMORY'] = [el]
                        elif ('rom' in el.lower()) or ('storage' in el.lower()):
                            if 'MEMORY' in dictSpecs and (el) not in dictSpecs['MEMORY']: dictSpecs['MEMORY'].append(el)
                            elif 'MEMORY' not in dictSpecs: dictSpecs['MEMORY'] = [el]
                        elif ('pgm' in el.lower()):
                            if 'MEMORY' in dictSpecs and (el) not in dictSpecs['MEMORY']: dictSpecs['MEMORY'].append(el)
                            elif 'MEMORY' not in dictSpecs: dictSpecs['MEMORY'] = [el]

                # Camera
                if ('data capture' in attr.lower()) and ('camera' in spec.lower()):
                    specList = spec.split(', ')
                    for el in specList:
                        match = re.findall('\d+[\.]*[\d+]*', el.lower())
                        if ('camera' in el.lower()) and ('front' not in el.lower()):
                            content = (match[0] + 'MP rear camera')
                            if 'CAMERA' in dictSpecs and (content) not in dictSpecs['CAMERA']: dictSpecs['CAMERA'].append(content)
                            elif 'CAMERA' not in dictSpecs: dictSpecs['CAMERA'] = [content]
                        elif ('front' in el.lower()):
                            content = (match[0] + 'MP front camera')
                            if 'CAMERA' in dictSpecs and (content) not in dictSpecs['CAMERA']: dictSpecs['CAMERA'].append(content)
                            elif 'CAMERA' not in dictSpecs: dictSpecs['CAMERA'] = [content]

                # IP RATING
                if (re.findall('ip\d{2,2}', spec.lower())):
                    match = re.findall('ip\d{2,2}', spec.lower())
                    if 'IP RATING' in dictSpecs and match[0].upper() not in dictSpecs['IP RATING']: dictSpecs['IP RATING'].append(match[0].upper())
                    elif 'IP RATING' not in dictSpecs: dictSpecs['IP RATING'] = [match[0].upper()]


                # Battery
                if ('power' in attr.lower()):
                    specList = spec.split(', ')
                    for el in specList:
                        match = re.findall('(?:\d*\.\d+\s{0,2}mAh|\d+\s{0,2}mAh)', el.replace(',',''))
                        if match:
                            if ('STD' in el) or ('standard' in el.lower()):
                                if 'BATTERY' in dictSpecs and (match[0].replace(',', '') + ' (standard)') not in dictSpecs['BATTERY']: dictSpecs['BATTERY'].append((match[0].replace(',', '')  + ' (standard)'))
                                elif 'BATTERY' not in dictSpecs: dictSpecs['BATTERY'] = [match[0].replace(',', '')  + ' (standard)']
                            elif ('EXT' in el) or ('extended' in el.lower()):
                                if 'BATTERY' in dictSpecs and (match[0].replace(',', '') + ' (extended)') not in dictSpecs['BATTERY']: dictSpecs['BATTERY'].append((match[0].replace(',', '')  + ' (extended)'))
                                elif 'BATTERY' not in dictSpecs: dictSpecs['BATTERY'] = [match[0].replace(',', '')  + ' (extended)']
                            elif ('optional' in el.lower().replace('-','')):
                                if 'BATTERY' in dictSpecs and (match[0].replace(',', '') + ' (optional)') not in dictSpecs['BATTERY']: dictSpecs['BATTERY'].append((match[0].replace(',', '')  + ' (optional)'))
                                elif 'BATTERY' not in dictSpecs: dictSpecs['BATTERY'] = [match[0].replace(',', '')  + ' (optional)']
                            elif ('backup' in el.lower().replace('-','')):
                                if 'BATTERY' in dictSpecs and (match[0].replace(',', '') + ' (back-up)') not in dictSpecs['BATTERY']: dictSpecs['BATTERY'].append((match[0].replace(',', '')  + ' (back-up)'))
                                elif 'BATTERY' not in dictSpecs: dictSpecs['BATTERY'] = [match[0].replace(',', '')  + ' (back-up)']
                            else:
                                if 'BATTERY' in dictSpecs and (match[0].replace(',', '')) not in dictSpecs['BATTERY']: dictSpecs['BATTERY'].append((match[0].replace(',', '')))
                                elif 'BATTERY' not in dictSpecs: dictSpecs['BATTERY'] = [match[0].replace(',', '')]


                # Scan rate
                if 'read rate' in spec.lower():
                    if 'SCAN RATE' in dictSpecs and spec.lstrip().rstrip() not in dictSpecs['SCAN RATE']: dictSpecs['SCAN RATE'].append(spec.lstrip().rstrip())
                    elif 'SCAN RATE' not in dictSpecs: dictSpecs['SCAN RATE'] = [spec.lstrip().rstrip()]




            if 'KEYPAD' in dictSpecs:
                for index, el in enumerate(dictSpecs['KEYPAD']):
                    dictSpecs['KEYPAD'][index] = dictSpecs['KEYPAD'][index].replace('alpha numeric', 'alphanumeric').replace('alpha-numeric', 'alphanumeric').replace('alpha num.', 'alphanumeric')
                    dictSpecs['KEYPAD'][index] = dictSpecs['KEYPAD'][index].replace('function numeric', 'functional numeric').replace('function-numeric', 'functional numeric').replace('func. num.', 'functional numeric').replace('functional-numeric', 'functional numeric')
                    dictSpecs['KEYPAD'][index] = dictSpecs['KEYPAD'][index].replace('function numeric', 'functional numeric').replace('function-numeric', 'functional numeric').replace('func. num.', 'functional numeric').replace('functional-numeric', 'functional numeric')
                    dictSpecs['KEYPAD'][index] = dictSpecs['KEYPAD'][index].replace('numeric calc.', 'numeric calculation')
                    dictSpecs['KEYPAD'][index] = dictSpecs['KEYPAD'][index].replace('vt emulator', 'VT emulator')


            # Get image
            try:
                divImg = parsed.find('div', {'class' : 'ngucarousel-items'})
                urlImage = divImg.find('img')['src']
            except:
                urlImage = None

            if urlImage:
                img = Image.open(requests.get(urlImage, stream = True).raw)

                imgName = nameProduct.replace('/','-')
                imgType = urlImage.split('.')[-1]
                img.save(f'static/img/{imgName}.{imgType}')
                imgDict[nameProduct] = imgName + '.' + imgType
            else:
                imgDict[nameProduct] = None

            #### Save all product data ####
            supplier = 'Point Mobile'
            dictProduct['supplier'] = supplier
            dictProduct['product-group'] = define_group(nameProduct, supplier.lower())
            dictProduct['product-name-type-only'] = nameProduct
            dictProduct['product-name'] = supplier + ' ' + nameProduct.replace('/','-')
            dictProduct['image'] = imgDict[nameProduct]
            dictProduct['accessories'] = baseURL + urlProduct


            driver.get(baseURL + urlProduct)
            btn = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Data Sheet')]")))
            btn.click()
            sleep(3)

            parsed = BeautifulSoup(driver.page_source, 'html5lib')
            links = [item['href'] for item in parsed.find_all('a', {'class': 'button--show_item' }) if (('quickstartguide' not in item['href'].lower().replace(' ','')) and ('https' in item['href']))]
            dictProduct['link'] = links[0]

            # Sort content keys
            for key in dictSpecs.keys(): dictSpecs[key] = sorted(dictSpecs[key])
            df = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in dictSpecs.items() ]))
            df = df.reindex(sorted(df.columns), axis=1)
            df = df.fillna(0)

            for key in df.columns:
                dictProduct[key] = df[key].to_list()

            # Check if product name in dataframe
            if not dfProduct[dfProduct['product-name'] == dictProduct['product-name']].empty:
                dictProduct['release-date'] = dfProduct.loc[dfProduct['product-name'] == dictProduct['product-name'], 'release-date'].values[0]
                newRow = pd.DataFrame.from_records([dictProduct])
                dfProduct.loc[dfProduct['product-name'] == dictProduct['product-name'], newRow.columns] = newRow.values
            else:
                dfProduct = pd.concat([dfProduct, pd.DataFrame.from_records([dictProduct])], ignore_index=True)

            #print(dfProduct)
            print("{} finished".format(nameProduct))


    dfProduct = dfProduct.fillna(0)

    depreciatedProducts = ['Honeywell Thor CV31']
    for p in depreciatedProducts:
        dfProduct = dfProduct.drop(dfProduct[dfProduct['product-name'] == p].index)

    return dfProduct


if __name__ == '__main__':
    with open('products.json', 'r') as f:
        products = json.load(f)
    scrapingPM(products)
