import xml.etree.cElementTree as ET
import re
import pprint
from collections import defaultdict

SAMPLE_OSMFILE = '../data/boston_cambridge.osm'

# detects street types as the last word in street name, plus optional period and whitespace
street_type_re = re.compile(r'\b\S+\.?\s*$', re.IGNORECASE)
# detects street numbers at beginning of street name
street_number_re = re.compile(r'^\d*\s+')


# normal street types
expected_types = set(['Avenue', 
                      'Boulevard', 
                      'Broadway', 
                      'Center', 
                      'Commons', 
                      'Court', 
                      'Drive',
                      'Driveway', 
                      'Highway',
                      'Lane', 
                      'Mall', 
                      'Park', 
                      'Parkway', 
                      'Place', 
                      'Plaza', 
                      'Road', 
                      'Row', 
                      'Square', 
                      'Street', 
                      'Terrace', 
                      'Trail', 
                      'Way',
                      'Wharf', 
                      'Yard'])

# normal street types for this area
expected_types_locale = set(['Fenway', 'Hall'])

# maps abbreviations and variations to canoncial street types
types_mapping = {'Ave': 'Avenue', 
                 'Ave.': 'Avenue', 
                 'Ct': 'Court',
                 'Hwy': 'Highway', 
                 'Pkwy': 'Parkway', 
                 'Pl': 'Place', 
                 'rd.': 'Road', 
                 'Rd': 'Road',
                 'Rd.': 'Road', 
                 'Sq.': 'Square', 
                 'st': 'Street', 
                 'St': 'Street',
                 'St.': 'Street',
                 'ST': 'Street'}

# street type errors that had to be manually corrected
types_corrections = {'Albany': 'Albany Street',
                     'Avenue De Lafayette': 'De Lafayette Avenue',
                     'Avenue Louis Pasteur': 'Louis Pasteur Avenue',
                     'Boylston': 'Boylston Street',
                     'Boylston Street, 5th Floor': 'Boylston Street', 
                     'Bromfield Street #501': 'Bromfield Street',  
                     'Cambrdige': 'Cambridge Street',
                     'Cambridge Street #1302': 'Cambridge Street',
                     'Charles Street South': 'Charles Street',
                     'Dartmouth ': 'Dartmouth Street',
                     'Dartmouth': 'Dartmouth Street',
                     'Faneuil Hall Market': 'Fanueil Hall',
                     'First Street, Suite 1100': 'First Street',
                     'First Street, Suite 303': 'First Street',
                     'First Street, 18th floor': 'First Street', 
                     'Franklin Street, Suite 1702': 'Franklin Street',
                     'Hampshire': 'Hampshire Street',
                     'Harvard St #12': 'Harvard Street',
                     'Kendall Square - 3': 'Kendall Square',
                     'LOMASNEY WAY, ROOF LEVEL': 'Lomasney Way',
                     'Longwood': 'Longwood Avenue',
                     'Newbury': 'Newbury Street',
                     'Sidney Street, 2nd floor': 'Sidney Street',
                     'South Market Building': 'Fanueil Hall',
                     'Stillings Street Garage': 'Stillings Street',
                     'Webster Street, Coolidge Corner': 'Webster Street',
                     'Windsor': 'Windsor Street',
                     'Winsor': 'Windsor Street'}

# street types errors that could not be corrected (due to lack of street information, i.e. not a formatting problem)
types_errors = set(['PO Box 846028', 'South Station, near Track 6'])

# helper functions
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def has_street_type(street_name):
    return street_type_re.search(street_name) is not None

def has_street_number(street_name):
    return street_number_re.search(street_name) is not None

def get_street_type(street_name):
    return street_type_re.search(street_name).group().strip()

def get_street_number(street_name):
    return street_number_re.search(street_name).group().strip()

# whether the street type is normal (either usually or for this locale)
def is_standard_street_type(street_name):
    street_type = get_street_type(street_name)
        
    return street_type in expected_types or street_type in expected_types_locale

# used for updating street names
def is_street_name_error(street_name):
    return street_name in types_errors

# detect and organize street names that do not match the canonical street type formatting
def audit_street_type(street_types, street_name):
    if has_street_type(street_name):
        street_type = get_street_type(street_name)
        
        if not is_standard_street_type(street_name):
            street_types[street_type].add(street_name)

# detect and organize street names that contain numbers in the start of the name
def audit_street_number(street_numbers, street_name):
    if has_street_number(street_name):
        street_number = get_street_number(street_name)
        
        street_numbers[street_number].add(street_name)

# parses xml file, detecting and organizing non-canonical street names by number and street type
def audit_street_names(osm_file):
    
    street_types = defaultdict(set)
    street_numbers = defaultdict(set)
    
    with open(osm_file, 'r') as osm_file:
        for event, elem in ET.iterparse(osm_file, events=('start',)):

            if elem.tag == 'node' or elem.tag == 'way':
                for tag in elem.iter('tag'):
                    if is_street_name(tag):
                        street_name =  tag.attrib['v']
                        
                        audit_street_type(street_types, street_name)
                        audit_street_number(street_numbers, street_name)
    
    return street_types, street_numbers

# used for updating street names; whether or not the street name needs to be changed, i.e. is not canonical
def needs_street_name_update(street_name):
    return ((has_street_type(street_name) and not is_standard_street_type(street_name) and
             not is_street_name_error(street_name)) or 
            has_street_number(street_name))

# updates street name by removing numbers and/or replacing non-canonical street types
def update_street_name(street_name):
    # corrections can't be handled by mapping, and are a subset of possible mapping cases, so do these first
    if street_name in types_corrections:
        street_name = types_corrections[street_name]
    elif has_street_type(street_name):
        street_type = get_street_type(street_name)
        
        # if there's an abbreviation that can be fixed by mapping, replace the abbreviation by the canonical form
        if street_type in types_mapping:
            street_name = street_type_re.sub(types_mapping[street_type], street_name)
    
    # remove any street numbers present in the street name
    if has_street_number(street_name):
        street_name = street_number_re.sub('', street_name)
    
    # also handles unknown cases, possibly new street names.  could throw error here
    return street_name