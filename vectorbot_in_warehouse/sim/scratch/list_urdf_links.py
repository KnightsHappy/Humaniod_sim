import xml.etree.ElementTree as ET

urdf_path = "/home/nihit/bots/Assembly_mass_replace/assembly_1_1/urdf/assembly_1_1.urdf"
tree_urdf = ET.parse(urdf_path)
root_urdf = tree_urdf.getroot()

print("All links in assembly_1_1.urdf:")
for link in root_urdf.findall('link'):
    name = link.get('name')
    inertial = link.find('inertial')
    has_inertial = inertial is not None
    print(f"Link: {name:40} | Has Inertial: {has_inertial}")
