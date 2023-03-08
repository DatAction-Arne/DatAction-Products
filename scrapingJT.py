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


def scrapingJT(products):
    if products is None:
        dfProduct = pd.DataFrame(columns=['release-date', 'supplier', 'product-group', 'product-name', 'product-name-type-only', 'image', 'link', 'accessories',
                                          'SCANNING', 'WIFI', 'WWAN', 'GPS', 'RESOLUTION', 'BLUETOOTH', 'NFC', 'OTHER', 'FREEZER MODEL', 'RFID', 'OS', 'KEYPAD', 'MEMORY', 'CAMERA', 'IP RATING',
                                          'BATTERY', 'SCAN RATE', 'SYSTEM INTERFACE', 'MEDIA WIDTH', 'SPEED', 'PRINT MODE', 'PRINT WIDTH'])
    else:
        dfProduct = pd.DataFrame.from_dict(products)


    baseURL = 'https://www.jarltech.com/2007/'

    imgDict = {}

    #### Find all product group urls ####
    for i in range(20):
        try:
            request = requests.get(urljoin(baseURL, 'index.php?language=en'), timeout=10)
            break
        except:
            print("Request failed.")
            sleep(0.1)


    parsed = BeautifulSoup(request.content, 'html5lib')
    listKeep = ['barcode readers', 'mobile terminals', 'label printers', 'pos printers', 'notebooks (rugged)', 'notebooks']
    hrefGroupList = [item['href'] for item in parsed.find_all('a', {'class': 'hauptkat' }) if item.text.replace('\xa0','').lower() in listKeep]
    nameGroupList = [item.text.replace('\xa0','') for item in parsed.find_all('a', {'class': 'hauptkat' }) if item.text.replace('\xa0','').lower() in listKeep]
    #print('Group url: {} \n'.format(hrefGroupList))
    #print('Group names: {} \n'.format(nameGroupList))

    #### Sub groups in product groups ####
    for urlGroup, nameGroup  in zip(hrefGroupList[0:], nameGroupList[0:]):
        for i in range(20):
            try:
                request = requests.get(urljoin(baseURL, urlGroup), timeout=10)
                break
            except:
                print("Request failed.")
                sleep(0.1)



        parsed = BeautifulSoup(request.content, 'html5lib')
        if 'notebooks' in nameGroup.lower():
            hrefSubgroupList = [urlGroup]
            nameSubgroupList = [nameGroup]
        else:
            listKeep = ['handheld readers', 'cordless scanners', 'headset terminals', 'vehicle mount terminals', 'handheld terminals', 'tablets', 'desktop printers', 'midrange printers', 'industrial printers', 'mobile printers', 'rfid printers']
            hrefSubgroupList = [item['href'] for item in parsed.find_all('a', {'class': 'subkat' }) if item.text.replace('\xa0','').lower() in listKeep]
            nameSubgroupList = [item.text.replace('\xa0','') for item in parsed.find_all('a', {'class': 'subkat' }) if item.text.replace('\xa0','').lower() in listKeep]
        #print('Subgroup url: {} \n'.format(hrefSubgroupList))
        #print('Subgroup names: {} \n'.format(nameSubgroupList))

        #### Products ####
        for urlSubgroup, nameSubgroup in zip(hrefSubgroupList[0:], nameSubgroupList[0:]):
            for i in range(20):
                try:
                    request = requests.get(urljoin(baseURL, urlSubgroup), timeout=10)
                    break
                except:
                    print("Request failed.")
                    sleep(0.1)


            parsed = BeautifulSoup(request.content, 'html5lib')

            listKeep = ['zebra', 'honeywell', 'datalogic', 'getac', 'panasonic', 'm3', 'point mobile', 'proglove']
            listOmit = ['captuvo']
            hrefProductList = [item['href'] for item in parsed.find_all('a', {'class': 'artikelkat' }) if ((item.text.split(' ')[0].lower() in listKeep or 'point mobile' in item.text.lower()) and not any([el for el in listOmit if el in item.text.lower()]))]
            nameProductList = [item.text.replace(' Series', '') for item in parsed.find_all('a', {'class': 'artikelkat' }) if ((item.text.split(' ')[0].lower() in listKeep or 'point mobile' in item.text.lower()) and not any([el for el in listOmit if el in item.text.lower()]))]
            #print('Products url: {} \n'.format(hrefProductList))
            #print('Products names: {} \n'.format(nameProductList))

            #### Product specs ####
            for urlProduct, nameProduct in zip(hrefProductList[0:], nameProductList[0:]):
                dictSpecs = {}
                dictProduct = {}
                for i in range(20):
                    try:
                        request = requests.get(urljoin(baseURL, urlProduct), timeout=10)
                        break
                    except:
                        print("Request failed.")
                        sleep(0.1)

                parsed = BeautifulSoup(request.content, 'html5lib')

                # Check if product name in dataframe
                if not dfProduct[dfProduct['product-name'] == nameProduct.replace('/','-')].empty:
                    print('{} Already in dataframe'.format(nameProduct.replace('/','-')))
                    #continue
                else:
                    dictProduct['release-date'] = datetime.today().strftime('%d-%m-%Y')

                # Get image
                try:
                    urlImage = parsed.find('img', {'id' : 'jt_sr_img'})['src']
                except:
                    urlImage = None

                if urlImage:
                    for i in range(20):
                        try:
                            img = Image.open(requests.get(urljoin('https://www.jarltech.com/', urlImage), stream = True).raw)
                            break
                        except:
                            print("Request failed.")
                            sleep(0.1)

                    imgName = nameProduct.replace('/','-')
                    imgType = urlImage.split('.')[-1]
                    img.save(f'static/img/{imgName}.{imgType}')
                    imgDict[nameProduct] = imgName + '.' + imgType
                else:
                    imgDict[nameProduct] = None

                # Data sheet link
                linkDatasheet = [item['href'] for item in parsed.find_all('a') if 'datasheet' in item.text.lower().replace(' ', '')]
                dictProduct['link'] = 'https://www.jarltech.com/' + linkDatasheet[0] if linkDatasheet else baseURL+urlProduct

                # Accesory guide link
                linkAccesories = [item['href'] for item in parsed.find_all('a') if 'accessoryguide' in item.text.lower().replace(' ', '')]
                dictProduct['accessories'] = 'https://www.jarltech.com/2007/' + linkAccesories[0] if linkAccesories else None

                # Initial check for certain specs
                contentProduct = [re.split('\,\s*(?![^()]*\))', item.text) for item in parsed.find_all("td")]
                contentProduct = list(chain.from_iterable(contentProduct))

                indexDrop1 = [i for i, val in enumerate(contentProduct) if 'Available Accessories' in val]
                if (len(indexDrop1) == 0):
                    indexDrop1.append(len(contentProduct))

                indexStart = [i for i, val in enumerate(contentProduct) if 'RSS Feed' in val]
                if (len(indexStart) == 0):
                    indexStart.append(0)

                contentProduct = contentProduct[indexStart[-1]:indexDrop1[0]]

                for index, spec in enumerate(contentProduct):
                    if 'handstrap' in spec.lower().replace('-', '').replace(' ', ''):
                        if 'OTHER' in dictSpecs and 'hand-strap' not in dictSpecs['OTHER']: dictSpecs['OTHER'].append('hand-strap')
                        elif 'OTHER' not in dictSpecs: dictSpecs['OTHER'] = ['hand-strap']
                    elif 'pistolgrip' in spec.lower().replace('-', '').replace(' ', ''):
                        if 'OTHER' in dictSpecs and 'pistol grip' not in dictSpecs['OTHER']: dictSpecs['OTHER'].append('pistol grip')
                        elif 'OTHER' not in dictSpecs: dictSpecs['OTHER'] = ['pistol grip']
                    elif 'hotswap' in spec.lower().replace('-', '').replace(' ', ''):
                        if 'OTHER' in dictSpecs and 'hot-swap' not in dictSpecs['OTHER']: dictSpecs['OTHER'].append('hot-swap')
                        elif 'OTHER' not in dictSpecs: dictSpecs['OTHER'] = ['hot-swap']
                    elif 'cordless' in spec.lower().replace('-', '').replace(' ', ''):
                        dictSpecs['CORDLESS'] = ['Supported']

                # Product page content
                contentProduct = [re.split('\,\s*(?![^()]*\))', item.text) for item in parsed.find_all("td")]

                # Create flat list
                contentProduct = list(chain.from_iterable(contentProduct))

                indexDrop2 = [i for i, val in enumerate(contentProduct) if 'Our top sellers' in val or 'All versions:' in val]
                if indexDrop2:
                    contentProduct = contentProduct[(indexDrop2[0]+1):indexDrop1[0]]
                else:
                    contentProduct = []

                if (len(contentProduct) == 0):
                    print('No content for ', nameProduct)

                # Specs
                for index, spec in enumerate(contentProduct):
                    # CORDLESS
                    if 'cordless' in spec.lower().replace('-', '').replace(' ', ''):
                        dictSpecs['CORDLESS'] = ['Supported']

                    # WIFI
                    if 'wi-fi' in spec.lower() or 'wlan' in spec.lower():
                        dictSpecs['WIFI'] = ['Supported']

                    # WWAN
                    elif ('4g' in spec.lower() and not '4gb' in spec.lower()) or ('5g' in spec.lower()) or (('sim' in spec.lower()) and (not 'zsim' in spec.lower()) and (not 'simple' in spec.lower())):
                        dictSpecs['WWAN'] = ['Supported']

                    # NFC
                    elif 'nfc' in spec.lower():
                        dictSpecs['NFC'] = ['Supported']

                    # GPS
                    elif 'gps' in spec.lower():
                        dictSpecs['GPS'] = ['Supported']

                    # FREEZER UNIT
                    elif 'freezer' in spec.lower() or 'cold storage' in spec.lower():
                        dictSpecs['FREEZER MODEL'] = ['Supported']

                    # Bluetooth
                    elif 'bt' in spec.lower() or 'bluetooth' in spec.lower():
                        dictSpecs['BLUETOOTH'] = ['Supported']

                    # RFID
                    elif 'rfid' in spec.lower():
                        dictSpecs['RFID'] = ['Supported']

                    # Scanning
                    elif ((index + 1) <= len(contentProduct)) and '2d' in spec.lower() and ('standard range' in contentProduct[index+1] or 'SR' in contentProduct[index+1]):
                        if 'SCANNING' in dictSpecs and '2D standard range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('2D standard range imager')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['2D standard range imager']
                    elif ((index + 1) <= len(contentProduct)) and '2d' in spec.lower() and ('extended range' in contentProduct[index+1] or 'ER' in contentProduct[index+1] or 'long range' in contentProduct[index+1] or 'LR' in contentProduct[index+1]):
                        if 'SCANNING' in dictSpecs and '2D extended range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('2D extended range imager')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['2D extended range imager']
                    elif ((index + 1) <= len(contentProduct)) and '2d' in spec.lower() and ('medium range' in contentProduct[index+1] or 'MR' in contentProduct[index+1]):
                        if 'SCANNING' in dictSpecs and '2D medium range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('2D medium range imager')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['2D medium range imager']
                    elif ((index + 1) <= len(contentProduct)) and '2d' in spec.lower() and ('wide angle' in contentProduct[index+1] or 'WA' in contentProduct[index+1]):
                        if 'SCANNING' in dictSpecs and '2D wide angle imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('2D wide angle imager')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['2D wide angle imager']
                    elif ((index + 1) <= len(contentProduct)) and '2d' in spec.lower() and ('FR' in contentProduct[index+1] or 'flexrange' in contentProduct[index+1].lower() or 'flex range' in contentProduct[index+1].lower()):
                        if 'SCANNING' in dictSpecs and '2D flex range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('2D flex range imager')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['2D flex range imager']
                    elif ((index + 1) <= len(contentProduct)) and '2d' in spec.lower() and 'EX20' in contentProduct[index+1]:
                        if 'SCANNING' in dictSpecs and '2D near/far imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('2D near/far imager')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['2D near/far imager']
                    elif ((index + 1) <= len(contentProduct)) and '1d' in spec.lower() and ('standard range' in contentProduct[index+1] or 'SR' in contentProduct[index+1]):
                        if 'SCANNING' in dictSpecs and '1D standard range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('1D standard range imager')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['1D standard range imager']
                    elif ((index + 1) <= len(contentProduct)) and '1d' in spec.lower() and ('extended range' in contentProduct[index+1] or 'ER' in contentProduct[index+1] or 'long range' in contentProduct[index+1] or 'LR' in contentProduct[index+1]):
                        if 'SCANNING' in dictSpecs and '1D extended range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('1D extended range imager')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['1D extended range imager']
                    elif ((index + 1) <= len(contentProduct)) and '1d' in spec.lower() and ('medium range' in contentProduct[index+1] or 'MR' in contentProduct[index+1]):
                        if 'SCANNING' in dictSpecs and '1d medium range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('1d medium range imager')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['1d medium range imager']
                    elif ((index + 1) <= len(contentProduct)) and '2d' in spec.lower() and 'imager' in contentProduct[index+1].lower():
                        if 'SCANNING' in dictSpecs and '2D standard range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('2D standard range imager')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['2D standard range imager']
                    elif ((index + 1) <= len(contentProduct)) and '1d' in spec.lower() and ('imager' in contentProduct[index+1] or 'laser' in contentProduct[index+1]):
                        if 'SCANNING' in dictSpecs and '1D standard range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('1D standard range imager')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['1D standard range imager']
                    elif ((index + 1) <= len(contentProduct)) and '1d' in spec.lower() and ('omnidirectional' in contentProduct[index+1] or 'CCD' in contentProduct[index+1]):
                        if 'SCANNING' in dictSpecs and '1D standard range imager' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('1D standard range imager')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['1D standard range imager']
                    elif 'dpm' in spec.lower():
                        if 'SCANNING' in dictSpecs and 'DPM Support' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('DPM Support')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['DPM Support']
                    elif 'digimarc' in spec.lower():
                        if 'SCANNING' in dictSpecs and 'Digimarc Support' not in dictSpecs['SCANNING']: dictSpecs['SCANNING'].append('Digimarc Support')
                        elif 'SCANNING' not in dictSpecs: dictSpecs['SCANNING'] = ['Digimarc Support']

                    # Keypad
                    elif 'keypad' in spec.lower():
                        match = re.findall('\((.*)\)', spec)
                        #print(spec)
                        if match:
                            #print("KEYPAD MATCH")
                            if 'KEYPAD' in dictSpecs and match[0].lower().replace(', backlight', '') not in dictSpecs['KEYPAD']: dictSpecs['KEYPAD'].append(match[0].lower().replace(', backlight', ''))
                            elif 'KEYPAD' not in dictSpecs: dictSpecs['KEYPAD'] = [match[0].lower().replace(', backlight', '')]

                    # OS
                    elif 'android ' in spec.lower():
                        match = re.findall('\((.{1,4})\)', spec)
                        if match:
                            if 'OS' in dictSpecs and ('Android ' + match[0]) not in dictSpecs['OS']: dictSpecs['OS'].append('Android ' + match[0])
                            elif 'OS' not in dictSpecs: dictSpecs['OS'] = ['Android ' + match[0]]
                        else:
                            if 'OS' in dictSpecs and 'Android' not in dictSpecs['OS']: dictSpecs['OS'].append('Android')
                            elif 'OS' not in dictSpecs: dictSpecs['OS'] = ['Android']
                    elif (re.search(r'\b' + 'win' + r'\b', spec.lower()) or re.search(r'\b' + 'windows' + r'\b', spec.lower())):
                        match = re.findall('\d{3,}', spec)
                        if match:
                            for el in match:
                                spec = spec.replace(el, '')
                        if 'embedded' in spec.lower() or 'iot' in spec.lower() or 'enterprise' in spec.lower() or 'ce' in spec.lower() or 'mobile' in spec.lower():
                            if 'OS' in dictSpecs and spec not in dictSpecs['OS']: dictSpecs['OS'].append(spec)
                            elif 'OS' not in dictSpecs: dictSpecs['OS'] = [spec]


                    # Memory
                    elif 'ram:' in spec.lower():
                        splitted = spec.split(':')
                        if 'MEMORY' in dictSpecs and (' '.join(splitted[1:]).replace(' ','').lstrip().rstrip()) + ' RAM' not in dictSpecs['MEMORY']: dictSpecs['MEMORY'].append(''.join(splitted[1:]).replace(' ','').lstrip().rstrip() + ' RAM')
                        elif 'MEMORY' not in dictSpecs: dictSpecs['MEMORY'] = [''.join(splitted[1:]).replace(' ','').lstrip().rstrip() + ' RAM']
                    elif 'flash:' in spec.lower():
                        splitted = spec.split(':')
                        if 'MEMORY' in dictSpecs and (' '.join(splitted[1:]).replace(' ','').lstrip().rstrip() + ' ROM') not in dictSpecs['MEMORY']: dictSpecs['MEMORY'].append(''.join(splitted[1:]).replace(' ','').lstrip().rstrip() + ' ROM')
                        elif 'MEMORY' not in dictSpecs: dictSpecs['MEMORY'] = [''.join(splitted[1:]).replace(' ','').lstrip().rstrip() + ' ROM']

                    # Camera
                    elif 'webcam' in spec.lower():
                        if 'CAMERA' in dictSpecs and 'front camera' not in dictSpecs['CAMERA']: dictSpecs['CAMERA'].append('front camera')
                        elif 'CAMERA' not in dictSpecs: dictSpecs['CAMERA'] = ['front camera']
                    elif 'front cam' in spec.lower():
                        match = re.findall('^.*?\([^\d]*(\d+)[^\d]*\).*$', spec.lower())
                        #print(match)
                        if match:
                            if 'CAMERA' in dictSpecs and (match[0] + 'MP front camera') not in dictSpecs['CAMERA']: dictSpecs['CAMERA'].append(match[0] + 'MP front camera')
                            elif 'CAMERA' not in dictSpecs: dictSpecs['CAMERA'] = [match[0] + 'MP front camera']
                        else:
                            if 'CAMERA' in dictSpecs and 'front camera' not in dictSpecs['CAMERA']: dictSpecs['CAMERA'].append('front camera')
                            elif 'CAMERA' not in dictSpecs: dictSpecs['CAMERA'] = ['front camera']
                    elif 'cam' in spec.lower() and not 'webcam' in spec.lower():
                        match = re.findall('^.*?\([^\d]*(\d+)[^\d]*\).*$', spec.lower())
                        #print(match)
                        if match:
                            if 'CAMERA' in dictSpecs and (match[0] + 'MP rear camera') not in dictSpecs['CAMERA']: dictSpecs['CAMERA'].append(match[0] + 'MP rear camera')
                            elif 'CAMERA' not in dictSpecs: dictSpecs['CAMERA'] = [match[0] + 'MP rear camera']
                        else:
                            if 'CAMERA' in dictSpecs and 'rear camera' not in dictSpecs['CAMERA']: dictSpecs['CAMERA'].append('rear camera')
                            elif 'CAMERA' not in dictSpecs: dictSpecs['CAMERA'] = ['rear camera']

                    # IP RATING
                    elif re.findall('ip\d{2,2}', spec.lower()):
                        match = re.findall('ip\d{2,2}', spec.lower())
                        if 'IP RATING' in dictSpecs and match[0].upper() not in dictSpecs['IP RATING']: dictSpecs['IP RATING'].append(match[0].upper())
                        elif 'IP RATING' not in dictSpecs: dictSpecs['IP RATING'] = [match[0].upper()]

                    # Other
                    elif 'handstrap' in spec.lower().replace('-', '').replace(' ', ''):
                        if 'OTHER' in dictSpecs and 'hand-strap' not in dictSpecs['OTHER']: dictSpecs['OTHER'].append('hand-strap')
                        elif 'OTHER' not in dictSpecs: dictSpecs['OTHER'] = ['hand-strap']
                    elif 'pistolgrip' in spec.lower().replace('-', '').replace(' ', ''):
                        if 'OTHER' in dictSpecs and 'pistol grip' not in dictSpecs['OTHER']: dictSpecs['OTHER'].append('pistol grip')
                        elif 'OTHER' not in dictSpecs: dictSpecs['OTHER'] = ['pistol grip']
                    elif 'hotswap' in spec.lower().replace('-', '').replace(' ', ''):
                        if 'OTHER' in dictSpecs and 'hot-swap' not in dictSpecs['OTHER']: dictSpecs['OTHER'].append('hot-swap')
                        elif 'OTHER' not in dictSpecs: dictSpecs['OTHER'] = ['hot-swap']

                    # Battery
                    elif re.findall('(?:\d*\.\d+\s{0,2}mAh|\d+\s{0,2}mAh)', spec):
                        match = re.findall('(?:\d*\.\d+\s{0,2}mAh|\d+\s{0,2}mAh)', spec)
                        if 'BATTERY' in dictSpecs and match[0].replace(' ', '') not in dictSpecs['BATTERY']: dictSpecs['BATTERY'].append(match[0].replace(' ', ''))
                        elif 'BATTERY' not in dictSpecs: dictSpecs['BATTERY'] = [match[0].replace(' ', '')]

                    # Scan rate
                    elif 'scan rate' in spec.lower():
                        if 'SCAN RATE' in dictSpecs and spec.split(':')[1].lstrip().rstrip() not in dictSpecs['SCAN RATE']: dictSpecs['SCAN RATE'].append(spec.split(':')[1].lstrip().rstrip())
                        elif 'SCAN RATE' not in dictSpecs: dictSpecs['SCAN RATE'] = [spec.split(':')[1].lstrip().rstrip()]

                    # Printer specs
                    # elif 'resolution' in spec.lower():
                    #     if 'RESOLUTION' in dictSpecs and spec.split(':')[1].lstrip().rstrip() not in dictSpecs['RESOLUTION']: dictSpecs['RESOLUTION'].append(spec.split(':')[1].lstrip().rstrip())
                    #     elif 'RESOLUTION' not in dictSpecs: dictSpecs['RESOLUTION'] = [spec.split(':')[1].lstrip().rstrip()]
                    elif re.findall('\d{1,3}\s{0,2}dots/mm\s{0,2}\(\d{2,4}\s{0,2}dpi\)', spec.lower()):
                        match =  re.findall('\d{1,3}\s{0,2}dots/mm\s{0,2}\(\d{2,4}\s{0,2}dpi\)', spec.lower())
                        if 'RESOLUTION' in dictSpecs and match[0] not in dictSpecs['RESOLUTION']: dictSpecs['RESOLUTION'].append(match[0])
                        elif 'RESOLUTION' not in dictSpecs: dictSpecs['RESOLUTION'] = [match[0]]
                    elif 'media width' in spec.lower():
                        if 'MEDIA WIDTH' in dictSpecs and spec.split(':')[1].lstrip().rstrip() not in dictSpecs['MEDIA WIDTH']: dictSpecs['MEDIA WIDTH'].append(spec.split(':')[1].lstrip().rstrip())
                        elif 'MEDIA WIDTH' not in dictSpecs: dictSpecs['MEDIA WIDTH'] = [spec.split(':')[1].lstrip().rstrip()]
                    elif 'print width' in spec.lower():
                        if 'PRINT WIDTH' in dictSpecs and spec.split(':')[1].lstrip().rstrip() not in dictSpecs['PRINT WIDTH']: dictSpecs['PRINT WIDTH'].append(spec.split(':')[1].lstrip().rstrip())
                        elif 'PRINT WIDTH' not in dictSpecs: dictSpecs['PRINT WIDTH'] = [spec.split(':')[1].lstrip().rstrip()]
                    elif 'diameter' in spec.lower():
                        if 'ROLL DIAMETER' in dictSpecs and spec.split(':')[1].lstrip().rstrip() not in dictSpecs['ROLL DIAMETER']: dictSpecs['ROLL DIAMETER'].append(spec.split(':')[1].lstrip().rstrip())
                        elif 'ROLL DIAMETER' not in dictSpecs: dictSpecs['ROLL DIAMETER'] = [spec.split(':')[1].lstrip().rstrip()]
                    elif ('speed' in spec.lower() or re.findall('\d{0,4}\.{0,1}\d{0,2}\s{0,2}mm/s', spec.lower())) and ('mm/s' in spec.lower()):
                        if ':' in spec:
                            if 'SPEED' in dictSpecs and spec.split(':')[1].lstrip().rstrip() not in dictSpecs['SPEED']: dictSpecs['SPEED'].append(spec.split(':')[1].lstrip().rstrip())
                            elif 'SPEED' not in dictSpecs: dictSpecs['SPEED'] = [spec.split(':')[1].lstrip().rstrip()]
                        else:
                            if 'SPEED' in dictSpecs and spec.lstrip().rstrip() not in dictSpecs['SPEED']: dictSpecs['SPEED'].append(spec.lstrip().rstrip())
                            elif 'SPEED' not in dictSpecs: dictSpecs['SPEED'] = [spec.lstrip().rstrip()]
                    elif 'cutter' in spec.lower():
                        if 'OTHER' in dictSpecs and 'cutter' not in dictSpecs['OTHER']: dictSpecs['OTHER'].append('cutter')
                        elif 'OTHER' not in dictSpecs: dictSpecs['OTHER'] = ['cutter']
                    elif 'peeler' in spec.lower():
                        if 'OTHER' in dictSpecs and 'peeler' not in dictSpecs['OTHER']: dictSpecs['OTHER'].append('peeler')
                        elif 'OTHER' not in dictSpecs: dictSpecs['OTHER'] = ['peeler']
                    elif 'rewinder' in spec.lower():
                        if 'OTHER' in dictSpecs and 'rewinder' not in dictSpecs['OTHER']: dictSpecs['OTHER'].append('rewinder')
                        elif 'OTHER' not in dictSpecs: dictSpecs['OTHER'] = ['rewinder']
                    elif 'thermal transfer' in spec.lower():
                        if 'PRINT MODE' in dictSpecs and 'thermal transfer' not in dictSpecs['PRINT MODE']: dictSpecs['PRINT MODE'].append('thermal transfer')
                        elif 'PRINT MODE' not in dictSpecs: dictSpecs['PRINT MODE'] = ['thermal transfer']
                    elif 'direct thermal' in spec.lower():
                        if 'PRINT MODE' in dictSpecs and 'direct thermal' not in dictSpecs['PRINT MODE']: dictSpecs['PRINT MODE'].append('direct thermal')
                        elif 'PRINT MODE' not in dictSpecs: dictSpecs['PRINT MODE'] = ['direct thermal']


                    # Interfaces
                    if 'usb' in spec.lower():
                        if 'SYSTEM INTERFACE' in dictSpecs and 'USB' not in dictSpecs['SYSTEM INTERFACE']: dictSpecs['SYSTEM INTERFACE'].append('USB')
                        elif 'SYSTEM INTERFACE' not in dictSpecs: dictSpecs['SYSTEM INTERFACE'] = ['USB']
                    if 'rs232' in spec.lower().replace(' ', '').replace('-',''):
                        if 'SYSTEM INTERFACE' in dictSpecs and 'RS-232' not in dictSpecs['SYSTEM INTERFACE']: dictSpecs['SYSTEM INTERFACE'].append('RS-232')
                        elif 'SYSTEM INTERFACE' not in dictSpecs: dictSpecs['SYSTEM INTERFACE'] = ['RS-232']
                    if 'kbw' in spec.lower():
                        if 'SYSTEM INTERFACE' in dictSpecs and 'Keyboard Wedge' not in dictSpecs['SYSTEM INTERFACE']: dictSpecs['SYSTEM INTERFACE'].append('Keyboard Wedge')
                        elif 'SYSTEM INTERFACE' not in dictSpecs: dictSpecs['SYSTEM INTERFACE'] = ['Keyboard Wedge']
                    if 'parallel' in spec.lower():
                        if 'SYSTEM INTERFACE' in dictSpecs and 'Parallel' not in dictSpecs['SYSTEM INTERFACE']: dictSpecs['SYSTEM INTERFACE'].append('Parallel')
                        elif 'SYSTEM INTERFACE' not in dictSpecs: dictSpecs['SYSTEM INTERFACE'] = ['Parallel']
                    if 'ethernet' in spec.lower():
                        if 'SYSTEM INTERFACE' in dictSpecs and 'Ethernet' not in dictSpecs['SYSTEM INTERFACE']: dictSpecs['SYSTEM INTERFACE'].append('Ethernet')
                        elif 'SYSTEM INTERFACE' not in dictSpecs: dictSpecs['SYSTEM INTERFACE'] = ['Ethernet']
                    if 'PoE' in spec or 'power over ethernet' in spec.lower():
                        if 'SYSTEM INTERFACE' in dictSpecs and 'PoE' not in dictSpecs['SYSTEM INTERFACE']: dictSpecs['SYSTEM INTERFACE'].append('PoE')
                        elif 'SYSTEM INTERFACE' not in dictSpecs: dictSpecs['SYSTEM INTERFACE'] = ['PoE']



                if 'KEYPAD' in dictSpecs:
                    for index, el in enumerate(dictSpecs['KEYPAD']):
                        dictSpecs['KEYPAD'][index] = dictSpecs['KEYPAD'][index].replace('alpha numeric', 'alphanumeric').replace('alpha-numeric', 'alphanumeric').replace('alpha num.', 'alphanumeric')
                        dictSpecs['KEYPAD'][index] = dictSpecs['KEYPAD'][index].replace('function numeric', 'functional numeric').replace('function-numeric', 'functional numeric').replace('func. num.', 'functional numeric').replace('functional-numeric', 'functional numeric')
                        dictSpecs['KEYPAD'][index] = dictSpecs['KEYPAD'][index].replace('function numeric', 'functional numeric').replace('function-numeric', 'functional numeric').replace('func. num.', 'functional numeric').replace('functional-numeric', 'functional numeric')
                        dictSpecs['KEYPAD'][index] = dictSpecs['KEYPAD'][index].replace('numeric calc.', 'numeric calculation')
                        dictSpecs['KEYPAD'][index] = dictSpecs['KEYPAD'][index].replace('vt emulator', 'VT emulator')


                #### Save all product data ####
                if nameProduct.lower().startswith('m3'):
                    supplier = 'M3'
                    dictProduct['supplier'] = supplier
                    dictProduct['product-group'] = define_group(' '.join(nameProduct.split(' ')[2:]), supplier.lower())
                    dictProduct['product-name-type-only'] = (' '.join(nameProduct.split(' ')[1:])).replace('/','-')
                elif 'point mobile' in nameProduct.lower():
                    dictProduct['supplier'] = supplier
                    dictProduct['product-group'] = define_group(' '.join(nameProduct.split(' ')[2:]), supplier.lower())
                    dictProduct['product-name-type-only'] = (' '.join(nameProduct.split(' ')[1:])).replace('/','-')
                else:
                    supplier = nameProduct.split(' ')[0]
                    dictProduct['supplier'] = supplier
                    dictProduct['product-group'] = define_group(' '.join(nameProduct.split(' ')[1:]), supplier.lower())
                    dictProduct['product-name-type-only'] = (' '.join(nameProduct.split(' ')[1:])).replace('/','-')
                #dictProduct['series-name'].append(seriesName)
                dictProduct['product-name'] = nameProduct.replace('/','-')
                dictProduct['image'] = imgDict[nameProduct]

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
                    dfProduct.loc[(dfProduct['product-name'] == dictProduct['product-name']), newRow.columns] = newRow.values
                else:
                    dfProduct = pd.concat([dfProduct, pd.DataFrame.from_records([dictProduct])], ignore_index=True)

                print("{} finished".format(nameProduct))


    dfProduct = dfProduct.fillna(0)

    depreciatedProducts = ['Honeywell Thor CV31', 'Honeywell VM2', 'Honeywell CN75-CN75e', 'Datalogic Skorpio X4', 'Datalogic Falcon X4', 'Zebra MT2000', 'Zebra MC3200', 'Zebra MC9200']
    for p in depreciatedProducts:
        dfProduct = dfProduct.drop(dfProduct[dfProduct['product-name'] == p].index)

    return dfProduct


if __name__ == '__main__':
    scrapingJT()
