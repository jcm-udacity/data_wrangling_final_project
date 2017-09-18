# Use cElementTree or lxml if too slow
import xml.etree.ElementTree as ET

OSM_FILE = '../data/boston_cambridge.osm'
SAMPLE_FILE = '../data/sample_10_boston_cambridge.osm'

# Parameter: take every k-th top level element
k = 10

def get_element(osm_file, tags=('node', 'way', 'relation')):
    '''
    Yield element if it is the right type of tag

    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    '''
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

if __name__ == '__main__:
    with open(SAMPLE_FILE, 'wb') as output:
        output.write(bytes("<?xml version='1.0' encoding='UTF-8'?>\n", 'utf-8'))
        output.write(bytes('<osm>\n', 'utf-8'))

        # Write every kth top level element
        for i, element in enumerate(get_element(OSM_FILE)):
            if i % k == 0:
                output.write(ET.tostring(element, encoding='utf-8'))

        output.write(bytes('</osm>', 'utf-8'))

