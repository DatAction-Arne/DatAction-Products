import requests
import json
import re
import html5lib
import numpy as np
import pandas as pd
import itertools
from bs4 import BeautifulSoup
from operator import is_not
from functools import partial
from PIL import Image
from utils import *


def scrapingZebra():

    baseURL = 'https://www.zebra.com'
    dictProduct = { 'supplier' : [], 'product-group' : [], 'series-name' : [], 'product-name' : [], 'product-name-type-only' : [], 'image' : [], 'specs' : [] , 'link' : [], 'accessories' : []}
    imgDict = {}

    #### Find all product group urls ####
    request = requests.get(baseURL + '/us/en/products.html')
    parsed = BeautifulSoup(request.content, 'html5lib')
    hrefGroup = [item['href'] for item in parsed.find_all("a", {'class': ['secondary left-button', 'textLinkH4'] })]
    # Omit groups #
    listOmit = ['supplies', 'location-technologies', 'interactive-kiosk', 'software', 'oem', 'temperature-monitoring-sensing', 'connect.zebra', 'Printing Supplies']
    hrefGroup = [i for i in hrefGroup if not any(x in i for x in listOmit)]
    #print('Group url: {} \n'.format(hrefGroup))

    #hrefGroup = ['/us/en/products/mobil:-computers.html', '/us/en/products/accessories.html']
    #### Sub groups in product groups ####
    for groupURL in hrefGroup[0:1]:
        if 'tablets' not in groupURL:
            request = requests.get(baseURL + groupURL)
            parsed = BeautifulSoup(request.content, 'html5lib')
            subhrefGroup = [item['href'] for item in parsed.find_all("a", {'class' : 'textLinkH4' }) if item.text not in omit_subgroup_zebra()]
            if 'accessories' in groupURL:
                dictProduct['accessories'] = [None]*len(dictProduct['supplier'])
            #print('Subgroup url: {} \n'.format(subhrefGroup))
        else:
            subhrefGroup = [groupURL]

        nameSubgroup = [item.text for item in parsed.find_all("a", {'class' : 'textLinkH4' }) if item.text not in omit_subgroup_zebra()]
        #print('Subgroup names: {} \n'.format(nameSubgroup))

        #### Product series ####
        for subgroupURL in subhrefGroup[0:1]:
            request = requests.get(baseURL + subgroupURL)
            parsed = BeautifulSoup(request.content, 'html5lib')

            if 'accessories' in groupURL:
                sectionSeries = parsed.find_all("a", {'class' : "secondary left-button"})
                namesSeries = [item.text.replace("Vehicle Mounted Computer", "VC8300 VC80x") for item in sectionSeries]
                hrefSeries = [item['href'] for item in sectionSeries]
            else:
                sectionSeries = parsed.find_all("div", {'class' : "productseries section"})
                namesSeries = [item.find('h2') for item in sectionSeries if not any(x in item.find('h2').text for x in omit_series_zebra())]
                namesSeries = [(' '.join(item.get_text(strip=True).split())).partition(' ')[0] for item in namesSeries]
                hrefSeries = [item.find('a')['href'] for item in sectionSeries if not any(x in item.find('h2').text for x in omit_series_zebra())]

            #print('Series names: {} \n'.format(namesSeries))

            #### Device types in product series ####
            for seriesURL, seriesName in zip(hrefSeries, namesSeries):
                # Associate accessory guide pdf with product
                if 'accessories' in groupURL:
                    if any(item in seriesName for item in dictProduct['product-name-type-only']):
                        print(seriesName)
                        index = [i for i in range(0, len(dictProduct['product-name-type-only'])) if dictProduct['product-name-type-only'][i] in seriesName]
                        for j in index:
                            dictProduct['accessories'][j] = baseURL+seriesURL
                    elif any(item in seriesName for item in dictProduct['series-name']):
                        print(seriesName)
                        index = [i for i in range(0, len(dictProduct['series-name'])) if dictProduct['series-name'][i] in seriesName]
                        for j in index:
                            dictProduct['accessories'][j] = baseURL+seriesURL
                    continue

                else:
                    request = requests.get(baseURL + seriesURL)
                    parsed = BeautifulSoup(request.content, 'html5lib')

                    products = [item for item in parsed.find_all("div", {'class' : 'productoverview section'}) if not any(x in item.find('h2').text for x in omit_product_zebra())]

                    nameProduct = [item.find('h2') for item in products]
                    nameProduct = [' '.join(item.get_text(strip=True).split()).replace("Zebra ", "").replace("Symbol ", "").replace("/"," ") for item in nameProduct]
                    typeonlyProduct = [item.partition(' ')[0] for item in nameProduct]

                    imageProduct = [item.find('img')['srcset'] for item in products]

                    all_aProduct = [item.find_all("a", {'ztype' : ['en', 'en-us', 'product-information']}) for item in products]
                    # Take specsheet in English (US)
                    all_hrefProduct = [[i['href'] for i in all_aProduct[j] if i['href'].startswith('/us')] for j in range(0,len(all_aProduct))]
                    all_pdfProduct = [[i['href'] for i in all_aProduct[j] if (i['href'].endswith('pdf') and 'spanish' not in i.text.lower())] for j in range(0,len(all_aProduct))]

                    if not all_hrefProduct or not [nameProduct[0]]:
                        print('No usual dataformatting for ', seriesURL)

                    #print('Product url: {} \n'.format(all_hrefProduct))
                    #print('Product name: {} \n'.format(nameProduct))


                #### Product specs ####
                for allProduct, name, image, pdfProduct in zip(all_hrefProduct, nameProduct, imageProduct, all_pdfProduct):
                    # Empty spec sheet link (probably redirect to pdf)
                    if len(allProduct) == 0:
                        print('--------------- \n Empty link for {} \n --------------'.format(name))
                        # Check if product name in dataframe
                        if name in dictProduct['product-name']:
                            print('Already in dataframe')
                            break

                        # Get product name & image link
                        img = Image.open(requests.get(baseURL + image, stream = True).raw)
                        imgType = img.format
                        imgName = name.replace('/','-').replace("*", "")
                        img.save(f'img/{imgName}.{imgType}')
                        imgDict[name] = imgName + '.' + imgType

                        #### Save all product data ####
                        dictProduct['supplier'].append('Zebra')
                        dictProduct['product-group'].append(define_group(name, "Zebra"))
                        dictProduct['series-name'].append(seriesName)
                        dictProduct['product-name'].append(name)
                        dictProduct['product-name-type-only'].append(name.partition(' ')[0])
                        dictProduct['image'].append(imgDict[name])
                        if manual_specs_zebra(name) is not None:
                            specs = manual_specs_zebra(name)
                            specs.columns = map(str.upper, specs.columns)
                        else:
                            specs = pd.concat([pd.DataFrame({'PDF' : {"0" : 'Beschikbaar via site van leverancier (zie boven)'}})] , ignore_index=True)
                            specs.columns = map(str.upper, specs.columns)
                            print('Empty specs')

                        dictProduct['specs'].append(specs.to_dict())

                        ######################### TODO: link to pdf #########################
                        #####################################################################
                        dictProduct['link'].append(baseURL+pdfProduct[0])
                        #####################################################################

                        print("{} finished".format(name))

                    for urlProduct in allProduct:
                        request = requests.get(baseURL + urlProduct)
                        parsed = BeautifulSoup(request.content, 'html5lib')

                        ## Multiple specsheet in product overview ##
                        if len(allProduct) > 1:
                            name = name + '-' + parsed.find("h1").text.replace("/"," ")

                        # Check if product name in dataframe
                        if name in dictProduct['product-name']:
                            print('Already in dataframe')
                            break

                        # Get product name & image link
                        try:
                            img = Image.open(requests.get(baseURL + image, stream = True).raw)
                            imgType = img.format
                            imgName = name.replace('/','-')
                            img.save(f'img/{imgName}.{imgType}')
                            imgDict[name] = imgName + '.' + imgType
                        except:
                            imgDict[name] = None

                        # Table names
                        namesTable = [item.text for item in parsed.find_all("span", { 'class' : 'spec-sheet-caption'})]
                        namesTableFilter = [el for el in namesTable if el not in omit_tables_zebra()]

                        # Filter table names if different product
                        for col in namesTable:
                            if (name.split(' ')[0] not in col and any(x in col for x in nameProduct)):
                                namesTableFilter.remove(col)

                        # Get index filtered names
                        filt = []
                        filt = list(np.where(np.isin(namesTable, namesTableFilter))[0])

                        # Content tables
                        tables = list(map(parsed.find_all("table").__getitem__, filt))
                        #print(namesTableFilter)

                        #### Get all table data ####
                        dfList = []
                        indexFilter = []
                        i = 0
                        for table in tables:

                            contentTable = [item.text for item in table.find_all("td")]

                            # Get attributes (and delete \n character)
                            attr = list(map(lambda each:each.strip('\n'), contentTable[::2]))
                            # Split string according to delimeters
                            contentAttr = [re.split('; |;|\n|,', item) for item in contentTable[1::2]]
                            # Remove empty strings
                            contentAttr = [list(filter(None, item)) for item in contentAttr]
                            dictTable = dict(zip(attr, contentAttr))
                            # Create df
                            df = pd.DataFrame(dict([(k,pd.Series(v)) for k,v in dictTable.items() ]))


                            # Delete attributes of different product type (e.g. all specs of EC55 if product is EC50)
                            for col in df.columns:
                                # delete line in table if spec is related to other type or not in filter_attributes
                                if (not search_string(col, name.split(' ')[0], ['/', '(', ')', ';', ':'], ' ') and any(x in col for x in typeonlyProduct)):
                                    df = df.drop(columns=col)
                                else:
                                    # Flag to skip next line if line is related to other product
                                    skip = False

                                    # Check attribute content
                                    for j in range(0, len(df.loc[:, col])):
                                        content = str(df.loc[:, col][j])
                                        name_type_only = name.partition(' ')[0]
                                        # If product type is not in the attribute & another product type is => drop the line from the table
                                        # Search for exact matches with re.search()
                                        if (not search_string(content, name_type_only, ['/', '(', ')', ';', ':'], ' ') and any(x in content for x in typeonlyProduct) and not skip_content_zebra(col)):
                                            df.loc[:, col][j] = np.nan
                                            skip = True
                                            #print("Spec: {} \t Product type: {} \t Content: {}".format(col, name, content))
                                        elif (search_string(content, name_type_only, ['/', '(', ')', ';', ':'], ' ')):
                                            skip = False
                                            #print('Device : {} \t Attribute : {} \t Content : {}'.format(name.split(' '), col, content))
                                        elif (not any(x in content for x in nameProduct) and skip):
                                            if not skip_line_zebra(col):
                                                df.loc[:, col][j] = np.nan
                                                #print("Spec: {} \t Product type: {} \t Content: {}".format(col, name, content))
                                            else:
                                                skip = False

                                    # Delete attribute if content is emtpy
                                    if (df.loc[:, col].isnull().all()):
                                        df = df.drop(columns=col)

                            # Keep only specific set of attributes
                            for col in df.columns:
                                maskAttr = [(el, attr[1], attr[2]) for attr in filter_attributes() for el in attr[0] if (search_string(col.lower(), el) and col.lower() not in filter_attributes_skip())]
                                if not maskAttr:
                                    df = df.drop(columns=col)
                                # If 3rd field in mask => this content should be in table
                                elif maskAttr and maskAttr[0][2]:
                                    if maskAttr[0][2] == 'check content':
                                        matchContent = [el for el in filter_content() if (maskAttr[0][0] == el[0] and [i for i in el[1] if any(df[col].str.contains(i, case=False).dropna())])]
                                        if matchContent:
                                            df = df.drop(col, axis=1)
                                            df.loc[0, col] = matchContent[0][3]
                                            df = df.rename(columns={col : matchContent[0][2].upper()})
                                        else:
                                            df = df.drop(columns=col)
                                    else:
                                        df = df.drop(col, axis=1)
                                        df.loc[0, col] = maskAttr[0][2]
                                        df = df.rename(columns={col : maskAttr[0][1].upper()})
                                # If no 3rd field in mask => keep original content
                                elif maskAttr and not maskAttr[0][2]:
                                    df = df.rename(columns={col : maskAttr[0][1].upper()})


                            # Append index of empty dataframe to list to delete later
                            if df.isnull().values.all():
                                indexFilter.append(i)

                            df = df.loc[:,~df.columns.duplicated()]
                            dfList.append(df.to_dict())
                            i += 1

                        #print('Names len: {} \t \t Table len: {}'.format(len(namesTableFilter), len(dfList)))
                        #df = pd.DataFrame([dfList], columns = namesTableFilter)

                        #### Save all product data ####
                        dictProduct['supplier'].append('Zebra')
                        dictProduct['product-group'].append(define_group(name, "Zebra"))
                        dictProduct['series-name'].append(seriesName)
                        dictProduct['product-name'].append(name)
                        dictProduct['product-name-type-only'].append(name.partition(' ')[0])
                        dictProduct['image'].append(imgDict[name])
                        #dictProduct['specs'].append(df.to_json())

                        # Check if list not empty and Concatenate list of dataframes and remove duplicate columns
                        if dfList:
                            specs = pd.concat([pd.DataFrame(df) for df in dfList], axis=1)
                            specs = specs.loc[:,~specs.columns.duplicated()]
                            specs.dropna(axis = 0, how = 'all', inplace = True)
                        else:
                            specs = pd.concat([pd.DataFrame({'attr1' : {"0" : 'empty'}}), pd.DataFrame({'attr2' : {"0" : 'empty'}})], axis=1, ignore_index=True)

                        specs = specs.reindex(sorted(specs.columns), axis=1)

                        dictProduct['specs'].append(specs.to_dict())
                        dictProduct['link'].append(baseURL+urlProduct)
                        print("{} finished".format(name))

    return dictProduct

    with open('test.json', 'w') as fp:
        json.dump(dictProduct, fp)
