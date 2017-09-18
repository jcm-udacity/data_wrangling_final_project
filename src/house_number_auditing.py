import xml.etree.cElementTree as ET
import re
import pprint
from collections import defaultdict

SAMPLE_OSMFILE = '../data/boston_cambridge.osm'

# detects single house number, i.e. non-leading zero 5 digit number (unless the number is zero) with optional capital
# letter or 1/2 following
single = '([1-9]\d{0,4}|0)([A-Z]| 1/2)?'
# detects single house numbers as standalone, chained by ',' (up to 5 house numbers), or connected by '-'  for 
# consecutive ranges of house numbers
house_numbers_re_string = '^' + single + '((-' + single + ')?|(,' + single + '){0,4})$'

house_numbers_re = re.compile(house_numbers_re_string)

# house number errors that need to be manually corrected
house_numbers_corrections = {'17/19': '17,19', 
                             '33, 33 1/2': '33,33 1/2', 
                             '34,36a,36b': '34,36A,36B', 
                             '4 Suite S-1155': '4', 
                             '6; 8': '6,8', 
                             '84; 86': '84,86', 
                             'One': '1', 
                             'Ten': '10', 
                             'Zero': '0'}

# house number errors that could not be corrected (due to lack of house number information, i.e. not a formatting 
# problem)
house_numbers_errors = set(['Building 22', 'PO Box 846028'])

# helper functions
def is_house_number(elem):
    return (elem.attrib['k'] == "addr:housenumber")

# whether the house number is well formed (according to the regular expression above)
def is_standard_house_number(house_number):
    return house_numbers_re.search(house_number) is not None

# used for updating house number errors
def is_house_number_error(house_number):
    return house_number in house_numbers_errors

# detect and organize house numbers that are not well formed
def audit_house_number_anomaly(house_number_anomalies, house_number):
    if not is_standard_house_number(house_number):
        house_number_anomalies.add(house_number)

# parses xml file, detecting and organizing non-well formed house numbers
def audit_house_numbers(osm_file):
    
    house_number_anomalies = set()
    
    with open(osm_file, 'r') as osm_file:
        for event, elem in ET.iterparse(osm_file, events=('start',)):

            if elem.tag == 'node' or elem.tag == 'way':
                for tag in elem.iter('tag'):
                    if is_house_number(tag):
                        audit_house_number_anomaly(house_number_anomalies, tag.attrib['v'])
    
    return house_number_anomalies

# used for updating house numbers; whether or not the house number needs to be changed, i.e. is not well formed
def needs_house_number_update(house_number):
    return not (is_standard_house_number(house_number) or is_house_number_error(house_number))

# updates house numbers by replacing non-canonical punctuation (';' or '-', in the case of it being otherwise well 
# formed) or manually correcting the entire house number (in the case of complicated cases)
def update_house_number(house_number):
    
    # for sequences of housing numbers using ';' instead of ','
    if house_numbers_re.search(house_number.replace(';', ',')):
        return house_number.replace(';', ',')
    # for consecutive ranges of housing numbers using ':' instead of '-'
    elif house_numbers_re.search(house_number.replace(':', '-')):
        return house_number.replace(':', '-')
    # for cases needing manual correction
    elif house_number in house_numbers_corrections:
        return house_numbers_corrections[house_number]
    # also handles unknown cases, possibly new house numbers.  could throw error here
    else:
        return house_number