import xml.etree.ElementTree as ET

urdf_path = "/home/nihit/bots/Assembly_mass_replace/assembly_1_1/urdf/assembly_1_1.urdf"
tree = ET.parse(urdf_path)
root = tree.getroot()

print("All links in assembly_1_1.urdf:")
for link in root.findall('link'):
    name = link.get('name')
    inertial = link.find('inertial')
    if inertial is not None:
        mass = inertial.find('mass').get('value')
        origin = inertial.find('origin')
        origin_xyz = origin.get('xyz') if origin is not None else "N/A"
        print(f"Link: {name:40} | Mass: {mass:10} | Origin XYZ: {origin_xyz}")
    else:
        print(f"Link: {name:40} | Mass: None (No inertial tag)")
