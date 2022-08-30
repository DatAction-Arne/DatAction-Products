import numpy as np
import re
import pandas as pd

# Replace characters in string s
def replace_characters(s, char_from, char_to):
    for i in range(0, len(char_from)):
        s.replace(char_from[i], char_to)
    return s

# Search exact match of substring 'name' in string s
def search_string(s, name, char_from = '', char_to = ''):
    if not char_from and not char_to:
        return re.search(r'\b' + name + r'\b', s)
    else:
        return re.search(r'\b' + name + r'\b', replace_characters(s, char_from, char_to))


# Search duplicates
def search_and_combine(names, tables):
    names = np.array(names)
    tables = np.array(tables)

    for el in names:
        indices = np.where(names == el)[0]
        if len(indices) > 1:
            names = np.delete(names, indices[1:])
            combined_dict = {key:val for d in tables[indices] for key,val in d.items()}
            tables[indices[0]] = combined_dict

    return list(names), list(tables)


# Define groupname of product based on type
def define_group(name, supplier):
    if supplier == "zebra":
        if (name.upper().startswith('MC') or
            name.upper().startswith('PS') or
            name.upper().startswith('MT') or
            name.upper().startswith('TC8')):
            subgroup = 'handterminals'
        elif (name.upper().startswith('TC') or
            name.upper().startswith('EC') or
            name.upper().startswith('M60')):
            subgroup = 'pda'
        elif (name.upper().startswith('WT') or
            name.upper().startswith('RS') or
            name.upper().startswith('HD') or
            name.upper().startswith('WS')):
            subgroup = 'wearable-computers'
        elif (name.upper().startswith('ET') or
            name.upper().startswith('XBOOK') or
            name.upper().startswith('XSLATE') or
            name.upper().startswith('XPAD') or
            'L10' in name.upper() or
            'R12' in name.upper()):
            subgroup = 'tablets'
        elif name.upper().startswith('VC'):
            subgroup = 'heftruck-terminals'
        elif name.upper().startswith('HS'):
            subgroup = 'voice'
        elif (name.upper().startswith('RFD') or
             name.upper().startswith('FX') or
             name.upper().startswith('ST') or
             name.upper().startswith('AN') or
             name.upper().startswith('SR') or
             name.upper().startswith('SP') or
             name.upper().startswith('ATR') or
             name.upper().startswith('SN')):
            subgroup = 'rfid'
        elif (name.upper().startswith('ZT') or
             name.upper().startswith('ZQ') or
             name.upper().startswith('ZD') or
             name.upper().startswith('ZXP') or
             name.upper().startswith('ZC') or
             name.upper().startswith('TLP') or
             name.upper().startswith('GX') or
             name.upper().startswith('GK') or
             name.upper().startswith('GT') or
             'XI4' in name.upper()):
            subgroup = 'printers'
        elif (name.upper().startswith('DS') or
             name.upper().startswith('LI') or
             name.upper().startswith('LS') or
             name.upper().startswith('CS')):
            subgroup = 'barcodescanners'
        elif (name.upper().startswith('DS457') or
             name.upper().startswith('MP') or
             name.upper().startswith('MS') or
             name.upper().startswith('FS')):
            subgroup = 'fixed-scanners'
        else:
            subgroup = 'ERROR: SUBGROUP NOT FOUND'

    elif supplier == "honeywell":
        if ('SCANPAL' in name.upper() and 'EDA6' in name.upper() or
           name.upper().startswith('CK')):
            subgroup = 'handterminals'
        elif ((name.upper().startswith('CT')) or
             'DOLPHIN' in name.upper() or
             name.upper().startswith('CN') or
             'SCANPAL' in name.upper() and 'EDA6' not in name.upper() and 'EDA7' not in name.upper()):
            subgroup = 'pda'
        elif ('XENON' in name.upper() or
             'VOYAGER' in name.upper() or
             'FUSION' in name.upper() or
             'ECLIPSE' in name.upper() or
             name.upper().startswith('SF') or
             'HYPERION' in name.upper() or
             'GRANIT' in name.upper()):
            subgroup = 'barcodescanners'
        elif ('8670' in name.upper() or
             name.upper().endswith('I')):
            subgroup = 'wearable-computers'
        elif (name.upper().startswith('SCANPAL') and 'TABLET' in name.upper() or
             name.upper().startswith('RT') or
             name.upper().startswith('SCANPAL') and 'EDA7' in name.upper()):
            subgroup = 'tablets'
        elif ('THOR' in name.upper() or
            'VM' in name.upper()):
            subgroup = 'heftruck-terminals'
        elif ('VOICE' in name.upper() or
             'VOCOLLECT' in name.upper()):
            subgroup = 'voice'
        elif (name.upper().startswith('IH') or
             name.upper().startswith('IP') or
             name.upper().startswith('IF')):
            subgroup = 'rfid'
        elif ('PRINTER' in name.upper() or
             name.upper().startswith('PC') or
             name.upper().startswith('PM') or
             name.upper().startswith('PD') or
             name.upper().startswith('PX') or
             name.upper().startswith('RP') or
             name.upper().startswith('PR') or
             name.upper().startswith('PL') or
             name.upper().startswith('RL') or
             name.upper().startswith('PB') or
             name.upper().startswith('MP') or
             'E-CLASS' in name.upper() or
             'M-CLASS' in name.upper()):
            subgroup = 'printers'
        elif (name.upper().startswith('HF') or
             'GENESIS' in name.upper() or
             'ORBIT' in name.upper() or
             'VUQUEST' in name.upper() or
             'SOLARIS' in name.upper()):
            subgroup = 'fixed-scanners'
        else:
            subgroup = 'ERROR: SUBGROUP NOT FOUND'

    elif supplier == "datalogic":
        if ('SKORPIO' in name.upper() or
           'FALCON' in name.upper()):
            subgroup = 'handterminals'
        elif ('RHINO' in name.upper() or
           name.upper().startswith('SH')):
            subgroup = 'heftruck-terminals'
        elif ('MEMOR' in name.upper() or
           'JOYA TOUCH' in name.upper() or
           'DL-AXIST' in name.upper()):
            subgroup = 'pda'
        elif ('TASKBOOK' in name.upper()):
            subgroup = 'tablets'
        elif ('TOUCH' in name.upper() and 'TD' in name.upper() or
             'HERON' in name.upper() and 'HD' in name.upper() or
             'RIDA' in name.upper() or
             'GRYPHON' in name.upper() or
             'QUICKSCAN' in name.upper() or
             'HANDSCANNER' in name.upper() or
             name.upper().startswith('PD') or
             name.upper().startswith('PM') or
             name.upper().startswith('PB') or
             name.upper().startswith('PD')):
            subgroup = 'barcodescanners'
        elif (name.upper().startswith('DLR') or
             'RFID' in name.upper()):
            subgroup = 'rfid'
        else:
            subgroup = 'ERROR: SUBGROUP NOT FOUND'

    elif supplier == "m3":
        if (name.upper().startswith('US') or
            name.upper().startswith('UL')):
            subgroup = 'handterminals'
        elif ('RHINO' in name.upper() or
           name.upper().startswith('SH')):
            subgroup = 'heftruck-terminals'
        elif (name.upper().startswith('BK') or
            name.upper().startswith('OX') or
            name.upper().startswith('SM') or
            name.upper().startswith('SL')):
            subgroup = 'pda'
        else:
            subgroup = 'ERROR: SUBGROUP NOT FOUND'

    elif supplier == "panasonic":
        if (name.upper().startswith('TOUGHBOOK A') or
            name.upper().startswith('TOUGHBOOK G') or
            name.upper().startswith('TOUGHBOOK L') or
            name.upper().startswith('TOUGHBOOK S')):
            subgroup = 'tablets'
        elif (name.upper().startswith('TOUGHBOOK 33') or
            name.upper().startswith('TOUGHBOOK 55')):
            subgroup = 'rugged-laptops'
        elif (name.upper().startswith('TOUGHBOOK T') or
            name.upper().startswith('TOUGHBOOK N')):
            subgroup = 'pda'
        else:
            subgroup = 'ERROR: SUBGROUP NOT FOUND'

    elif supplier == "getac":
        if (name.upper().startswith('A') or
            name.upper().startswith('F') or
            name.upper().startswith('K') or
            name.upper().startswith('Z') or
            name.upper().startswith('Z') or
            name.upper().startswith('T') or
            name.upper().startswith('U')):
            subgroup = 'tablets'
        elif (name.upper().startswith('B') or
            name.upper().startswith('S') or
            name.upper().startswith('V') or
            name.upper().startswith('X')):
            subgroup = 'rugged-laptops'
        elif (name.upper().startswith('TOUGHBOOK T1') or
            name.upper().startswith('TOUGHBOOK N1')):
            subgroup = 'pda'
        else:
            subgroup = 'ERROR: SUBGROUP NOT FOUND'

    elif supplier == "proglove":
        subgroup = 'wearable-computers'

    elif supplier == "point mobile":
        if (re.findall('PM\d{3,3}', name.upper())):
            subgroup = 'handterminals'
        elif (re.findall('PM\d{2,2}', name.upper())):
            subgroup = 'pda'
        elif (re.findall('PM\d{1,1}', name.upper())):
            subgroup = 'wearable-computers'
        elif ('RF' in name.upper()):
            subgroup = 'rfid'
        else:
            subgroup = 'ERROR: SUBGROUP NOT FOUND'

    return subgroup

# change table names
def change_table_names():
    return {'Physical Characteristics' : ['Mechanical', 'Physical Characteristics'],
            'System Architecture' : ['System Architecture', 'Performance Characteristics', 'Data Capture', 'Zebra Interactive Sensor Technology', 'Interactive Sensor Technology (IST)', 'Wireless WAN, Data and VoiceCommunications (TC57x Only)',
                                     'Wireless WAN Data and Voice Communications (TC57 Only)'],
            'WLAN' : ['WLAN', 'Wireless LAN', 'Wireless Connectivity', 'Wireless PAN'],
            'Environmental' : ['Environmental', 'User Environment', 'Device Durability'],
            'Device Approvals and Compliance' : ['Device Approvals and Compliance', 'Additional Certifications And Approvals', 'Regulatory', 'Non-Incendive Version', 'Data Security', 'Government Security And Encrytion']
            }

# Attributes to show
def filter_attributes():
    return [(['dimensions', 'dimension'], 'dimensions', ''), (['weight'], 'weight', ''), (['wwan', 'cellular', 'sim', 'edge', 'lte', 'gsm & edge'], 'WWAN', 'Supported'), (['wlan', 'wireless lan', 'operating channels', 'wi-fi', 'wifi', '802.11'], 'WIFI', 'Supported'),
            (['bluetooth'], 'bluetooth', 'Supported'), (['operating system', 'os'], 'OS', ''), (['scanning', 'scan engine', 'scan engines', 'decode capabilities', 'decode capability', 'barcode types'], 'scanning', ''), (['memory'], 'memory', ''),
            (['keypad', 'keyboard'], 'keypad', ''), (['camera'], 'camera', ''), (['nfc', 'cnofmcm', 'cnofmc'], 'NFC', 'Supported'), (['freezer', 'cold storage unit', 'cold storage'], 'freezer unit', 'Supported'),
            (['gps'], 'gps', 'Supported'), (['outdoor'], 'outdoor unit', 'Supported'), (['operating temp', 'operating temperature'], '', 'check content'), (['1d'], '1D barcodes', 'Supported'), (['2d'], '2D barcodes', 'Supported'),
            (['digimarc'], 'Digimarc barcodes', 'Supported'), (['ocr'], 'OCR', 'Supported'), (['sealing', 'ip rating'], 'sealing', ''), (['supported host interfaces', 'host system interface', 'host system interfaces'], 'supported host interfaces', ''),
            (['print resolution', 'resolution'], 'resolution', ''), (['communications', 'communication'], 'communications', ''), (['print width'], 'print width', ''), (['print speed', 'printing speed', 'max. print speed'], 'print speed', ''),
            (['cutter'], 'cutter', 'Supported'), (['print method'], 'print method', ''), (['media width', 'label width'], 'media width', ''), (['media handling'], 'media handling', ''),
            (['beam scanning range'], 'beam scanning range' , ''), (['user interface', 'interface', 'interfaces'], 'user interface', ''), (['fastest read rate'], 'read rate', ''), (['host computer', 'compatible models', 'compatible host devices', 'host models'], 'host models', ''),
            (['host connection', 'direction connection'], 'host connection', ''), (['mass storage'], 'mass storage', ''), (['media roll size', 'media diameter', 'roll diameter', 'maximum diameter'], 'media roll diameter', ''),
            (['nominal read range'], 'read range', ''), (['connectivity'], 'connectivity', '')
            ]

# Some attributes are shown without content
def filter_attributes_without_content():
    return [(['wwan', 'cellular', 'sim'], 'WWAN', 'Supported'), (['wlan', 'wireless lan', 'data rates', 'data rate', 'operating channels'], 'WIFI', 'Supported'),
            (['bluetooth'], 'bluetooth', 'Supported'),
            (['nfc', 'cnofmcm', 'cnofmc'], 'NFC', 'Supported'), (['freezer', 'cold storage unit'], 'freezer unit', 'Supported'), (['gps'], 'gps', 'Supported'),
            (['cutter'], 'cutter', ''),

            ]

# Attributes to show
def filter_attributes_skip():
    return ['minimum element resolution', 'symbology/resolution',
            ]

def filter_content():
    return [('operating temp', ['freezer', 'cold storage unit'], 'cold storage unit', 'Supported'), ('operating temperature', ['freezer', 'cold storage unit'], 'cold storage unit', 'Supported')
            ]














##
