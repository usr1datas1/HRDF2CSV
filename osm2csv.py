import codecs
import xml.etree.ElementTree as ET

tree = ET.parse('data/stop_positions.osm')
root = tree.getroot()

result = {}

for node in root:
    uic_name, uic_ref = None, None
    for tag in node:

        if tag.attrib['k'] == 'uic_name':
            uic_name = tag.attrib['v']
            continue

        if tag.attrib['k'] == 'uic_ref':
            uic_ref = tag.attrib['v']
            continue
    if uic_ref in result.keys():
        result[uic_ref].append(uic_name)
    else:
        result[uic_ref] = [uic_name]

print(result['8503000'])
print(len(result['8503000']))

output_filename = 'data/stop_posisions.csv'

with codecs.open(output_filename, 'w+b', encoding='UTF-8') as f:
    f.write(u'\ufeff')
    f.write('"{}";"{}";"{}"\n'.format('uic_ref', 'uic_name', 'stop_positions_count'))

with codecs.open(output_filename, 'a+b', encoding='UTF-8') as f:
    for uic_ref in result.keys():
        f.write('"{}";"{}";"{}"\n'.format(uic_ref, result[uic_ref][0], len(result[uic_ref])))