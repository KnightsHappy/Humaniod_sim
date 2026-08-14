import xml.etree.ElementTree as ET

xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"
tree = ET.parse(xacro_path)
root = tree.getroot()

print("Joints in vector.xacro:")
for joint in root.findall('.//joint'):
    name = joint.get('name')
    parent = joint.find('parent').get('link')
    child = joint.find('child').get('link')
    print(f"Joint: {name:40} | Parent: {parent:30} | Child: {child}")
