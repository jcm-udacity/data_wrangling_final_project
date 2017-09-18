import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json

# contain error detection and cleaning functions for addr:street and addr:housenumber fields
import street_auditing as sa
import house_number_auditing as hna

SAMPLE_OSMFILE = '../data/boston_cambridge.osm'

# used for parsing tag keys
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# subkeys for the created dictionary
created = [ 'version', 'changeset', 'timestamp', 'user', 'uid']

# extracts an xml element and converts it to a json serializable form
def shape_element(element):
    node = {}
    
    # all parent element tags currently, but if new parent elements are added to the original database later, 
    # this will make sure they don't break the parsing logic
    if element.tag == 'node' or element.tag == 'way' or element.tag == 'relation':
        node['tag'] = element.tag
        node['created'] = {}
        
        # ways and relations don't have 'lat' or 'lon' attributes
        if element.tag == 'node':
            node['pos'] = [None, None]
        
        attrib = element.attrib
        
        for a in attrib:
            if a in created:
                if a == 'version':
                    node['created'][a] = int(attrib[a])
                else:
                    node['created'][a] = attrib[a]
            elif a == 'lat':
                node['pos'][0] = float(attrib[a])
            elif a == 'lon':
                node['pos'][1] = float(attrib[a])
            else:
                node[a] = attrib[a]
        
        for e in element.iter():
            if e.tag == 'tag':
                key = e.attrib['k']
                value = e.attrib['v']
                
                if not problemchars.search(key):
                    if lower_colon.match(key):
                        s = key.split(':')
                        
                        if len(s) <= 2 and s[0] == 'addr':
                            
                            if 'address' not in node:
                                node['address'] = {}
                                is_valid_address = True
                            
                            if s[1] == 'street':
                                # standard street names don't need fixing
                                if sa.is_standard_street_type(value):
                                    node['address']['street'] = value
                                # fixes fixable street names
                                elif sa.needs_street_name_update(value):
                                    node['address']['street'] = sa.update_street_name(value)
                                # will remove this address later since street name is non valid
                                elif sa.is_street_name_error(value):
                                    is_valid_address = False
                                # for unhandled street formats, such as new street names.  could throw an 
                                # error here
                                else:
                                    node['address']['street'] = value
                            elif s[1] == 'housenumber':
                                # standard house numbers don't need fixing
                                if hna.is_standard_house_number(value):
                                    node['address']['housenumber'] = value
                                # fixes fixable house numbers
                                elif hna.needs_house_number_update(value):
                                    node['address']['housenumber'] = hna.update_house_number(value)
                                # will remove this address later since the house number is non valid 
                                elif hna.is_house_number_error(value):
                                    is_valid_address = False
                                # for unhandled house number formats, such as new house numbers.  could throw 
                                # an error here
                                else:
                                    node['address']['housenumber'] = value
                            else:
                                node['address'][s[1]] = value
                    else:
                        if key == 'address':
                            node['addressstring'] = value
                        else:
                            node[key] = value
            elif e.tag == 'nd':
                if 'node_refs' not in node:
                    node['node_refs'] = []
                
                node['node_refs'].append(e.attrib['ref'])
            elif e.tag == 'member':
                if 'node_members' not in node:
                    # relation members are ordered according to the OSM spec; use a list
                    node['node_members'] = []
                
                # a relation's member only consists of attributes, so add this to the list of members
                node['node_members'].append(e.attrib)
        
        # remove non valid addresses (i.e. addresses with house number or street errors)
        if 'address' in node and not is_valid_address:
            node.pop('address', None)
        
        return node
    else:
        return None

# iterates through an xml file parse tree and writes converted json representation to file, with optional
# indentation for easier processing by humans
def process_map(file_in, pretty=False):
    file_out = '{0}.json'.format(file_in)
    data = []
    with codecs.open(file_out, 'w') as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+'\n')
                else:
                    fo.write(json.dumps(el) + '\n')
    return data

if __name__ == '__main__':
    data = process_map(SAMPLE_OSMFILE, True)