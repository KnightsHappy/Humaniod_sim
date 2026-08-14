import xml.etree.ElementTree as ET

urdf_path = "/home/nihit/bots/Assembly_mass_replace/assembly_1_1/urdf/assembly_1_1.urdf"
tree_urdf = ET.parse(urdf_path)
root_urdf = tree_urdf.getroot()

print("Joints in assembly_1_1.urdf:")
for joint in root_urdf.findall('joint'):
    name = joint.get('name')
    parent = joint.find('parent').get('link')
    child = joint.find('child').get('link')
    print(f"Joint: {name:40} | Parent: {parent:30} | Child: {child}")
