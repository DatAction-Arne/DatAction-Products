import os, sys, subprocess, platform
import numpy as np
import pandas as pd
import json
import ast
import urllib
import secrets
import pdfkit
from flask import Flask, render_template, url_for, request, redirect, session, make_response, send_from_directory

import gevent.pywsgi
from platformshconfig import Config

subgroups = [
            { 'product' : "Handterminals", 'image' : 'static/img/handterminal.jpg', 'url' : 'handterminals' },
            { 'product' : "Truckterminals", 'image' : 'static/img/heftruckterminal.jpg', 'url' : 'heftruck-terminals' },
            { 'product' : "Wearables", 'image' : 'static/img/wearablecomputer.jpg', 'url' : 'wearable-computers' },

            { 'product' : "Handheld computers (PDA)", 'image' : 'static/img/pda.jpg', 'url' : 'pda' },
            { 'product' : "Barcodescanners", 'image' : 'static/img/barcodescanners.jpg', 'url' : 'barcodescanners' },
            ##{ 'product' : "FIXED SCANNERS", 'image' : 'static/img/scanner.png', 'url' : 'fixed-scanners' },
            { 'product' : "Printers", 'image' : 'static/img/printer.jpg', 'url' : 'printers' },
            ##{ 'product' : "VOICE PICKING", 'image' : 'static/img/voice.jpg', 'url' : 'voice' },
            { 'product' : "Robuuste tablet PC's", 'image' : 'static/img/tablet.jpg', 'url' : 'tablets' },
            { 'product' : "Rugged laptop", 'image' : 'static/img/ruggedlaptop.jpg', 'url' : 'rugged-laptops' },
            ##{ 'product' : "TOUCH PC'S", 'image' : 'static/img/touchpc.png', 'url' : 'touch-pc' },
            { 'product' : "RFID", 'image' : 'static/img/rfid.jpg', 'url' : 'rfid' },
            ]

# Formatting
""""
    Columns: ['release-date', 'supplier', 'product-group', 'product-name', 'product-name-type-only', 'image', 'link', 'accessories',
              'SCANNING', 'WIFI', 'WWAN', 'GPS', 'RESOLUTION', 'BLUETOOTH', 'NFC', 'OTHER', 'FREEZER MODEL', 'RFID', 'OS', 'KEYPAD', 'MEMORY', 'CAMERA', 'IP RATING',
              'BATTERY', 'SCAN RATE', 'SYSTEM INTERFACE', 'CORDLESS', 'MEDIA WIDTH', 'SPEED', 'PRINT MODE', 'PRINT WIDTH', 'new']
"""

def reloadFile(file):
    f = open(file)
    data = json.load(f)
    urlList = [el['url'] for el in subgroups]
    products = pd.DataFrame(data)

    return products, urlList

global products, urlList
products = reloadFile('products.json')

def get_abslute_path(subfolder, path):
    if subfolder is None:
        return app.root_path
    else:
        return app.root_path + subfolder + path



app = Flask(__name__)
app.jinja_env.globals.update(get_abslute_path=get_abslute_path)
app.config["SECRET_KEY"] = secrets.token_urlsafe(7)

config = Config()

@app.route("/")
def start():
    return redirect(url_for('home'))

# @app.route("/login")
# def login():
#     return render_template('NA.html')
#
# @app.route("/profiel")
# def profile():
#     return render_template('NA.html')
#
# @app.route("/registreer")
# def register():
#     return render_template('NA.html')

@app.route("/home", methods=['GET', 'POST'])
def home():
    session['product-group'] = ''
    session['filter'] = {}
    global products, urlList
    products, urlList = reloadFile('products.json')
    if request.method == 'POST':
        #print(request.form)
        #print(request.form['searchInput'])
        return redirect(url_for('search', search=request.form['searchInput']))

    return render_template('home.html', products=subgroups, names=products['product-name'].tolist())

# @app.route("/<product_group>", methods=['GET', 'POST'])
# def product_group(product_group):
#     session['product-group'] = product_group
#     search = request.args.to_dict()
#     #print('search: ',search)
#
#     filter = init_filters(product_group)
#
#     if request.method == 'GET':
#         print('product_group', 'GET')
#         if (request.args.to_dict()['search']) and (search['search'] != 'reset'):
#             dict = (ast.literal_eval(request.args.to_dict()['search']))
#
#             session['filter'] = dict
#             productsFilter = products.loc[products['product-group'] == product_group]
#
#             # Get products based on filter
#             productsFilter = filter_items(dict, productsFilter)
#
#         else:
#             productsFilter = products.loc[products['product-group'] == product_group]
#
#         #print('search : ', search)
#         if search['search'] == '' or search['search'] == 'reset':
#             dict = {}
#         else:
#             dict = ast.literal_eval(search['search'])
#
#         return render_template('products.html',
#                                 iter=len(productsFilter),
#                                 products=productsFilter,
#                                 filter=filter,
#                                 product_group=product_group,
#                                 search=dict,
#                                 names=products['product-name'].tolist()
#                                 )
#     else:
#         print('product_group', 'POST')
#         search = request.form.to_dict()
#         return redirect(url_for('filter_group',
#                                 product_group=product_group,
#                                 search=search)
#                         )

@app.route("/<product_group>", methods=['GET', 'POST'])
def product_group(product_group):

    if request.method == 'POST':
        filter = request.form.to_dict()
        return redirect(url_for("filter_group", product_group = product_group, filter = filter))
    else:
        filter = request.args.to_dict()
        productsFilter = products.loc[products['product-group'] == product_group]
        init_filter = init_filters(product_group)
        return render_template('products.html',
                                iter=len(productsFilter),
                                products=productsFilter,
                                filter=init_filter,
                                product_group=product_group,
                                search=filter,
                                names=products['product-name'].tolist()
                                )


@app.route("/<product_group>/", methods=['GET', 'POST'])
def filter_group(product_group):

    if request.method == 'GET':
        # Transform string of dict to dict
        filter = ast.literal_eval(request.args.get('filter'))

        init_filter = init_filters(product_group)

        #Get products based on filter
        productsFilter = products.loc[products['product-group'] == product_group]
        productsFilter = filter_items(filter, productsFilter)

        return render_template('products.html',
                                iter=len(productsFilter),
                                products=productsFilter,
                                filter=init_filter,
                                product_group=product_group,
                                search=filter,
                                names=products['product-name'].tolist()
                                )
    else:
        filter = request.form.to_dict()
        return redirect(url_for("filter_group", product_group = product_group, filter = filter))


@app.route("/<product_group>/<product_name>", methods=['GET', 'POST'])
def item(product_name, product_group):
    session['product-group'] = product_group

    item = products.loc[products['product-name'] == product_name]
    colNames = []
    for col in item.columns:
        if (item.iloc[0][col] == 0) or (col in ['supplier', 'product-group', 'product-name', 'product-name-type-only', 'image', 'link', 'accessories', 'release-date', 'new']):
            continue
        else:
            colNames.append(col)
    item = item.reindex(sorted(item.columns), axis=1)
    return render_template('item.html',
                            item=item,
                            specs=item[sorted(colNames)],
                            names=products['product-name'].tolist()
                            )

@app.route("/zoeken/", methods=['GET'])
def search():
    search = request.args.to_dict()['search']
    #print(search)
    searchProducts = products.loc[products['supplier'].str.contains(search, case=False) | products['product-name'].str.contains(search, case=False)]
    return render_template('search.html',
                            products=searchProducts,
                            iter=len(searchProducts),
                            names=products['product-name'].tolist()
                            )


@app.route("/vergelijk/<product_name1>/<product_name2>", methods=['GET', 'POST'])
def compare(product_name1, product_name2):
    if request.method == 'GET':
        print(product_name1, product_name2)
        item1, specs1, product_name1, productComp1, item2, specs2, product_name2, productComp2 = compare_params(product_name1, product_name2)

        return render_template('compare.html',
                                item1=item1,
                                specs1=specs1,
                                product_name1=product_name1,
                                products1=productComp1,
                                names=products['product-name'].tolist(),
                                item2=item2,
                                specs2=specs2,
                                product_name2=product_name2,
                                products2=productComp2,
                                urlList=urlList
                                )
    else:
        if ('searchInput1' in request.form) and (request.form['searchInput1']) and (product_name2 not in urlList or not product_name2.startswith('search=')):
            search = request.form['searchInput1']
            product_name1 = 'search='+ search

        elif ('searchInput2' in request.form) and (request.form['searchInput2']) and (product_name1 not in urlList or not product_name1.startswith('search=')):
            search = request.form['searchInput2']
            product_name2 = 'search='+ search

        elif ('searchInput1' in request.form) and (request.form['searchInput1']) and (product_name2 in urlList or product_name2.startswith('search=')):
            search = request.form['searchInput1']
            product_name1 = 'search='+ request.form['searchInput1']

        elif ('searchInput2' in request.form) and (request.form['searchInput2']) and (product_name1 in urlList or product_name1.startswith('search=')):
            product_name2 = 'search='+ request.form['searchInput1']


        return redirect(url_for('compare', product_name1=product_name1, product_name2=product_name2))

@app.route("/download/<product_name1>/<product_name2>")
def download_pdf(product_name1, product_name2):
    item1, specs1, product_name1, productComp1, item2, specs2, product_name2, productComp2 = compare_params(product_name1, product_name2)

    rendered = render_template('downloadPDF.html', item1=item1, specs1=specs1, product_name1=product_name1, products1=productComp1, item2=item2, specs2=specs2, product_name2=product_name2, products2=productComp2, urlList=urlList)

    #path_wkhtmltopdf = r'C:\DatAction\Dataction-Product-Selection\requirements\wkhtmltopdf\bin\wkhtmltopdf.exe'
    #path_wkhtmltopdf = r'C:\Users\ArneVanErum\OneDrive - Dataction BV\Projecten\Product app\requirements\wkhtmltopdf\bin\wkhtmltopdf.exe'
    if platform.system() == "Windows":
        path_wkhtmltopdf = './requirements/wkhtmltopdf/bin/wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=os.environ.get('WKHTMLTOPDF_BINARY', path_wkhtmltopdf))
    else:
        os.environ['PATH'] += os.pathsep + os.path.dirname(sys.executable)
        WKHTMLTOPDF_CMD = subprocess.Popen(['which', os.environ.get('WKHTMLTOPDF_BINARY', 'wkhtmltopdf')], stdout=subprocess.PIPE).communicate()[0].strip()
        config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_CMD)

    options = {"enable-local-file-access": None, "orientation": "Landscape"}
    outFile = 'comparison_{}_{}.pdf'.format(product_name1.replace(' ', ''), product_name2.replace(' ', ''))
    pdf = pdfkit.from_string(rendered, False, configuration = config, options = options)
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "inline; filename="+outFile

    return response
    #return redirect(url_for('compare', product_name1=product_name1, product_name2=product_name2))

@app.route("/datasheet/pdf/<name>")
def datasheet(name):
    return send_from_directory('./static/pdf', name)

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


def compare_params(product_name1, product_name2):
    if (product_name1 not in urlList) and (not product_name1.startswith('search=')):
        product_group = products.loc[products['product-name']==product_name1]['product-group'].tolist()[0]
        productComp1 = filter_items(session.get('filter'), products.loc[products['product-group']==product_group])
        item1 = products.loc[products['product-name'] == product_name1]
        colNames = []
        for col in item1.columns:
            if (item1.iloc[0][col] == 0) or (col in ['supplier', 'product-group', 'product-name', 'product-name-type-only', 'image', 'link', 'accessories', 'release-date', 'new']):
                continue
            else:
                colNames.append(col)
        item1 = item1.reindex(sorted(item1.columns), axis=1)
        specs1 = item1[sorted(colNames)]
    else:
        item1 = ''
        specs1 = ''
        if product_name1.startswith('search='):
            search = product_name1.split('=')[1]
            productComp1 = products.loc[products['supplier'].str.contains(search, case=False) | products['product-name'].str.contains(search, case=False)]
        else:
            productComp1 = filter_items(session.get('filter'), products.loc[products['product-group']==product_name1])
            product_name1 = 'search='


    if (product_name2 not in urlList) and (not product_name2.startswith('search=')):
        product_group = products.loc[products['product-name']==product_name2]['product-group'].tolist()[0]
        productComp2 = filter_items(session.get('filter'), products.loc[products['product-group']==product_group])
        item2 = products.loc[products['product-name'] == product_name2]
        colNames = []
        for col in item2.columns:
            if (item2.iloc[0][col] == 0) or (col in ['supplier', 'product-group', 'product-name', 'product-name-type-only', 'image', 'link', 'accessories', 'release-date', 'new']):
                continue
            else:
                colNames.append(col)
        item2 = item2.reindex(sorted(item2.columns), axis=1)
        specs2 = item2[sorted(colNames)]
    else:
        item2 = ''
        specs2 = ''
        if product_name2.startswith('search='):
            search = product_name2.split('=')[1]
            productComp2 = products.loc[products['supplier'].str.contains(search, case=False) | products['product-name'].str.contains(search, case=False)]
        else:
            productComp2 = filter_items(session.get('filter'), products.loc[products['product-group']==product_name2])
            product_name2 = 'search='

    return item1, specs1, product_name1, productComp1, item2, specs2, product_name2, productComp2


def filter_items(dict, productsFilter):
    if type(dict is dict):
        #print('Before filter: ', len(productsFilter))
        list1, list2, list3, list4, list5, list6, list7, list8 = [], [], [], [], [], [], [], [],
        for key in dict.keys():
            if key in ['Datalogic', 'Getac', 'Honeywell', 'M3', 'Panasonic', 'Point Mobile', 'ProGlove', 'Zebra']:
                list1.append(key)
            elif key in ['2D standard range imager', '2D medium range imager', '2D extended range imager', '2D near/far imager', '2D wide angle imager', '2D flex range imager', '1D standard range imager', '1D medium range imager', '1D extended range imager',
                         'DPM Support', 'Digimarc Support']:
                list2.append(key)
            elif key in ['Voor', 'Achter']:
                list3.append('front') if key == 'Voor' else list3.append('rear')
            elif key in ['Android', 'Windows']:
                keyTemp = key
                if keyTemp == 'Windows':
                    keyTemp = 'Win'
                list4.append(keyTemp)
            elif key in ['IP40', 'IP41', 'IP42', 'IP52', 'IP54', 'IP64', 'IP65', 'IP67', 'IP68']:
                list5.append(key)
            elif key == 'Cordless':
                productsFilter = productsFilter.loc[productsFilter['CORDLESS'] != 0] if dict[key] == 'Y' else productsFilter.loc[productsFilter['CORDLESS'] == 0]
            elif key == 'WWAN (4G)':
                productsFilter = productsFilter.loc[productsFilter['WWAN'] != 0] if dict[key] == 'Y' else productsFilter.loc[productsFilter['WWAN'] == 0]
            elif key == 'WiFi':
                productsFilter = productsFilter.loc[productsFilter['WIFI'] != 0] if dict[key] == 'Y' else productsFilter.loc[productsFilter['WIFI'] == 0]
            elif key == 'Bluetooth':
                    productsFilter = productsFilter.loc[productsFilter['BLUETOOTH'] != 0] if dict[key] == 'Y' else productsFilter.loc[productsFilter['BLUETOOTH'] == 0]
            elif key == 'Freezer':
                    productsFilter = productsFilter.loc[productsFilter['FREEZER MODEL'] != 0] if dict[key] == 'Y' else productsFilter.loc[productsFilter['FREEZER MODEL'] == 0]
            elif key in ['Numeriek', 'Alphanumeriek', 'Functioneel numeriek', 'qwertz', 'fr-layout', 'us-layout', 'uk-layout', 'fdns-layout', 'qwerty', 'azerty']:
                if key == 'Numeriek':
                    list6.append('numeric')
                elif key == 'Alphanumeriek':
                    list6.append('alphanumeric')
                elif key == 'Functioneel numeriek':
                    list6.append('functional numeric')
                else:
                    list6.append(key)
            elif key in ['Thermal transfer', 'Direct thermal']:
                list7.append(key.lower())
            elif key in ['203 dpi', '300 dpi', '406 dpi', '600 dpi']:
                list8.append(key)


        if list1:
            productsFilter = productsFilter.loc[productsFilter['supplier'].isin(list1)]
        if list2:
            indexList = []
            for index, row in productsFilter.iterrows():
                if row['SCANNING'] !=0 and all(el in ', '.join(str(x) for x in row['SCANNING']) for el in list2):
                    indexList.append(index)
            productsFilter = productsFilter.loc[indexList]
        if list3:
            indexList = []
            for index, row in productsFilter.iterrows():
                if row['CAMERA'] !=0 and all(el in ', '.join(str(x) for x in row['CAMERA']) for el in list3):
                    indexList.append(index)
            productsFilter = productsFilter.loc[indexList]
        if list4:
            indexList = []
            for index, row in productsFilter.iterrows():
                if row['OS'] !=0 and all(el.lower() in ', '.join(str(x) for x in row['OS']).lower() for el in list4):
                    indexList.append(index)
            productsFilter = productsFilter.loc[indexList]
        if list5:
            indexList = []
            for index, row in productsFilter.iterrows():
                if row['IP RATING'] !=0 and all(el in ', '.join(str(x) for x in row['IP RATING']) for el in list5):
                    indexList.append(index)
            productsFilter = productsFilter.loc[indexList]
        if list6:
            indexList = []
            for index, row in productsFilter.iterrows():
                if row['KEYPAD'] !=0:
                    #print(row['KEYPAD'])
                    #print(any([s for s in row['KEYPAD'] if 'functional numeric' in str(s)]))
                    if ('functional numeric' in list6) and any([s for s in row['KEYPAD'] if 'functional numeric' in str(s)]):
                        indexList.append(index)
                    elif ('alphanumeric' in list6) and any([s for s in row['KEYPAD'] if 'alphanumeric' in str(s)]):
                        indexList.append(index)
                    elif ('numeric' in list6) and any([s for s in row['KEYPAD'] if 'numeric' in str(s)]):
                        indexList.append(index)
                    elif ('numeric' in list6) and any([s for s in row['KEYPAD'] if 'numeric' in str(s)]):
                        indexList.append(index)
                    elif ('fr-layout' in list6) and any([s for s in row['KEYPAD'] if 'fr-layout' in str(s)]):
                        indexList.append(index)
                    elif ('us-layout' in list6) and any([s for s in row['KEYPAD'] if 'us-layout' in str(s)]):
                        indexList.append(index)
                    elif ('uk-layout' in list6) and any([s for s in row['KEYPAD'] if 'uk-layout' in str(s)]):
                        indexList.append(index)
                    elif ('fdns-layout' in list6) and any([s for s in row['KEYPAD'] if 'fdns-layout' in str(s)]):
                        indexList.append(index)
                    elif ('azerty' in list6) and any([s for s in row['KEYPAD'] if 'azerty' in str(s)]):
                        indexList.append(index)
                    elif ('qwertz' in list6) and any([s for s in row['KEYPAD'] if 'qwertz' in str(s)]):
                        indexList.append(index)
                    elif ('qwerty' in list6) and any([s for s in row['KEYPAD'] if 'qwerty' in str(s)]):
                        indexList.append(index)
            productsFilter = productsFilter.loc[indexList]
        if list7:
            indexList = []
            for index, row in productsFilter.iterrows():
                if row['PRINT MODE'] !=0 and all(el in ', '.join(str(x) for x in row['PRINT MODE']) for el in list7):
                    indexList.append(index)
            productsFilter = productsFilter.loc[indexList]
        if list8:
            indexList = []
            for index, row in productsFilter.iterrows():
                if row['RESOLUTION'] !=0 and all(el.replace(' ', '') in (', '.join(str(x) for x in row['RESOLUTION'])).replace(' ','') for el in list8):
                    print(row['RESOLUTION'])
                    indexList.append(index)
            productsFilter = productsFilter.loc[indexList]

        return productsFilter
        #print('After filter: ', len(productsFilter))

    else:
        #print("Wrong data type")
        exit()


def init_filters(product_group):
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    filteredProducts = products.loc[products['product-group'] == product_group]


    if (product_group == 'handterminals' or
       product_group == 'pda' or
       product_group == 'heftruck-terminals' or
       product_group == 'wearable-computers' or
       product_group == 'tablets' or
       product_group == 'rfid' or
       product_group == 'touch-pc' or
       product_group == 'rugged-laptops'):
        filter = {'Leverancier' : ['Datalogic', 'Getac', 'Honeywell', 'M3', 'Panasonic', 'Point Mobile', 'ProGlove', 'Zebra'],
                  'Scan Engine' : ['2D standard range imager', '2D medium range imager', '2D extended range imager', '2D near/far imager', '2D wide angle imager', '2D flex range imager', '1D standard range imager', '1D medium range imager', '1D extended range imager',
                                   'DPM Support', 'Digimarc Support'],
                  'Toetsenbord' : ['Numeriek', 'Alphanumeriek', 'Functioneel numeriek', 'qwertz', 'fr-layout', 'us-layout', 'uk-layout', 'fdns-layout', 'qwerty', 'azerty'],
                  'OS' : ['Android', 'Windows'],
                  'Freezer' : ['Ja', 'Neen'],
                  'WiFi' : ['Ja', 'Neen'],
                  'WWAN (4G)' : ['Ja', 'Neen'],
                  'Bluetooth' : ['Ja', 'Neen'],
                  'Camera' : ['Voor', 'Achter'],
                  'IP Rating' : ['IP42', 'IP54', 'IP64', 'IP65', 'IP67', 'IP68']
                  }

        for key in filter.keys():
            keyNew = key.replace('Leverancier', 'supplier').replace('Scan Engine', 'SCANNING').replace('Toetsenbord', 'KEYPAD').replace('IP Rating', 'IP RATING').replace('Freezer', 'FREEZER MODEL').replace('WiFi', 'WIFI').replace('WWAN (4G)', 'WWAN').replace('Bluetooth', 'BLUETOOTH').replace('Camera', 'CAMERA')

            for el in filter[key][:]:
                elNew = el.replace('Numeriek', 'numeric').replace('Alphanumeriek', 'alphanumeric').replace('Functioneel numeriek', 'functional numeric')
                if elNew == 'Ja':
                    elNew = 'Supported'
                if elNew == 'Neen':
                    elNew = '0'
                if elNew == 'Voor':
                    elNew = 'front'
                if elNew == 'Achter':
                    elNew = 'rear'
                if elNew == 'Windows':
                    elNew = 'Win'

                if (elNew.lower() not in filteredProducts.loc[:, keyNew].to_string().lower()):
                    #print(keyNew, elNew, filteredProducts.loc[:, keyNew].to_string())
                    filter[key].remove(el)


    elif product_group == 'printers':
        filter = {'Leverancier' : ['Honeywell', 'Zebra'],
                  'Print modus' : ['Thermal transfer', 'Direct thermal'],
                  'Resolutie' : ['203 dpi', '300 dpi', '406 dpi', '600 dpi'],
                  # 'Mediabreedte' : ['0 mm', '200 mm'],
                  # 'Printbreedte' : ['0 mm', '250 mm'],
                  # 'Snelheid' : ['0 mm/s', '400 mm/s'],
                  'WiFi' : ['Ja', 'Neen'],
                  'Bluetooth' : ['Ja', 'Neen'],
                  'IP Rating' : ['IP54', 'IP64', 'IP65', 'IP67', 'IP68']
                  }
        for key in filter.keys():
            keyNew = key.replace('Leverancier', 'supplier').replace('Print modus', 'PRINT MODE').replace('Resolutie', 'RESOLUTION').replace('IP Rating', 'IP RATING').replace('Freezer', 'FREEZER MODEL').replace('WiFi', 'WIFI').replace('WWAN (4G)', 'WWAN').replace('Bluetooth', 'BLUETOOTH').replace('Camera', 'CAMERA')

            for el in filter[key][:]:
                elNew = el.replace('Numeriek', 'numeric').replace('Alphanumeriek', 'alphanumeric').replace('Functioneel numeriek', 'functional numeric')
                if elNew == 'Ja':
                    elNew = 'Supported'
                if elNew == 'Neen':
                    elNew = '0'
                if elNew == 'Voor':
                    elNew = 'front'
                if elNew == 'Achter':
                    elNew = 'rear'

                if (elNew.lower().replace(' ', '') not in filteredProducts.loc[:, keyNew].to_string().lower().replace(' ', '')):
                    #print(keyNew, elNew.lower().replace(' ', ''), filteredProducts.loc[:, keyNew].to_string())
                    filter[key].remove(el)

    elif product_group == 'barcodescanners':
        filter = {'Leverancier' : ['Datalogic', 'Honeywell', 'M3', 'Panasonic', 'ProGlove', 'Zebra'],
                  'Scan Engine' : ['2D standard range imager', '2D medium range imager', '2D extended range imager', '2D near/far imager', '2D wide angle imager', '2D flex range imager', '1D standard range imager', '1D medium range imager', '1D extended range imager',
                                   'DPM Support', 'Digimarc Support'],
                  'Cordless' : ['Ja', 'Neen'],
                  'WiFi' : ['Ja', 'Neen'],
                  'WWAN (4G)' : ['Ja', 'Neen'],
                  'Bluetooth' : ['Ja', 'Neen'],
                  'IP Rating' : ['IP40', 'IP41', 'IP42', 'IP52', 'IP54', 'IP64', 'IP65', 'IP67', 'IP68']
                  }
        for key in filter.keys():
            keyNew = key.replace('Leverancier', 'supplier').replace('Scan Engine', 'SCANNING').replace('IP Rating', 'IP RATING').replace('WiFi', 'WIFI').replace('WWAN (4G)', 'WWAN').replace('Bluetooth', 'BLUETOOTH').replace('Cordless', 'CORDLESS')

            for el in filter[key][:]:
                elNew = el.replace('Numeriek', 'numeric').replace('Alphanumeriek', 'alphanumeric').replace('Functioneel numeriek', 'functional numeric')
                if el == 'Ja':
                    elNew = 'Supported'
                if el == 'Neen':
                    elNew = '0'

                if (elNew.lower() not in filteredProducts.loc[:, keyNew].to_string().lower()):
                    #print(keyNew, elNew, filteredProducts.loc[:, keyNew].to_string())
                    filter[key].remove(el)
    else:
        filter = {'Leverancier' : ['Datalogic', 'Getac', 'Honeywell', 'M3', 'Panasonic', 'Point Mobile', 'ProGlove', 'Zebra'],
                  'Scan Engine' : ['2D standard range imager', '2D medium range imager', '2D extended range imager', '2D near/far imager', '2D wide angle imager', '2D flex range imager', '1D standard range imager', '1D medium range imager', '1D extended range imager',
                                   'DPM Support', 'Digimarc Support'],
                  'Toetsenbord' : ['Numeriek', 'Alphanumeriek', 'Functioneel numeriek', 'qwertz'],
                  'OS' : ['Android', 'Windows'],
                  'Freezer' : ['Ja', 'Neen'],
                  'WiFi' : ['Ja', 'Neen'],
                  'WWAN (4G)' : ['Ja', 'Neen'],
                  'Bluetooth' : ['Ja', 'Neen'],
                  'Camera' : ['Voor', 'Achter'],
                  'IP Rating' : ['IP42', 'IP54', 'IP64', 'IP65', 'IP67', 'IP68']
                  }

        for key in filter.keys():
            keyNew = key.replace('Leverancier', 'supplier').replace('Scan Engine', 'SCANNING').replace('Toetsenbord', 'KEYPAD').replace('IP Rating', 'IP RATING').replace('Freezer', 'FREEZER MODEL').replace('WiFi', 'WIFI').replace('WWAN (4G)', 'WWAN').replace('Bluetooth', 'BLUETOOTH').replace('Camera', 'CAMERA')

            for el in filter[key][:]:
                elNew = el.replace('Numeriek', 'numeric').replace('Alphanumeriek', 'alphanumeric').replace('Functioneel numeriek', 'functional numeric')
                if elNew == 'Ja':
                    elNew = 'Supported'
                if elNew == 'Neen':
                    elNew = '0'
                if elNew == 'Voor':
                    elNew = 'front'
                if elNew == 'Achter':
                    elNew = 'rear'
                if elNew == 'Windows':
                    elNew = 'Win'

                if (elNew.lower() not in filteredProducts.loc[:, keyNew].to_string().lower()):
                    #print(filteredProducts.loc[:, keyNew].to_string())
                    filter[key].remove(el)
    return filter




if __name__ == "__main__":
    #app.run(debug=True)
    http_server = gevent.pywsgi.WSGIServer(('127.0.0.1', 5000), app)
    http_server.serve_forever()
