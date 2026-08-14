import xml.etree.ElementTree as ET

xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"
tree = ET.parse(xacro_path)
root = tree.getroot()

base_link = None
for link in root.findall('.//link'):
    if link.get('name') == 'base_link':
        base_link = link
        break

if base_link is not None:
    print(f"base_link has {len(base_link.findall('visual'))} visual meshes:")
    for visual in base_link.findall('visual'):
        origin = visual.find('origin')
        xyz = origin.get('xyz') if origin is not None else "0 0 0"
        mesh = visual.find('geometry/mesh')
        filename = mesh.get('filename') if mesh is not None else "No mesh"
        print(f"  Mesh: {filename.split('/')[-1]} | XYZ: {xyz}")
else:
    print("base_link not found")
