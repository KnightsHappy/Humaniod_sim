import xml.etree.ElementTree as ET

xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"
tree = ET.parse(xacro_path)
root = tree.getroot()

for elem in root.iter():
    if elem.tag == 'link' or elem.tag.endswith('link'):
        name = elem.get('name')
        inertial = elem.find('inertial')
        if inertial is not None:
            # Reconstruct the string for inertial to print exactly
            inertial_str = ET.tostring(inertial, encoding='utf-8').decode('utf-8').strip()
            print(f"Link: {name}")
            print(inertial_str)
            print("="*40)
