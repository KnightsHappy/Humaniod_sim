import xml.etree.ElementTree as ET

xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"
tree = ET.parse(xacro_path)
root = tree.getroot()

print("Links in vector.xacro with NO inertial tag:")
for link in root.findall('.//link'):
    name = link.get('name')
    inertial = link.find('inertial')
    if inertial is None:
        print(f"Link: {name}")
