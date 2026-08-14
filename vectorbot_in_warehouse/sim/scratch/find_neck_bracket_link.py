import xml.etree.ElementTree as ET

xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"
tree = ET.parse(xacro_path)
root = tree.getroot()

for elem in root.iter():
    if elem.tag == 'link' or elem.tag.endswith('link'):
        name = elem.get('name')
        for mesh in elem.findall('.//mesh'):
            fn = mesh.get('filename')
            if fn and 'Neck_bracket.stl' in fn:
                print(f"Found Neck_bracket.stl in link: {name}")
