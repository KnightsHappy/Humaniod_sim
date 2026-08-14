import xml.etree.ElementTree as ET

tree = ET.parse('/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro')
root = tree.getroot()

root_link = next(l for l in root.findall('link') if l.get('name') == 'root')
visuals = root_link.findall('visual')

for i, vis in enumerate(visuals):
    mesh = vis.find('geometry').find('mesh')
    if mesh is not None and 'ID_Needle_AXK_3047.stl' in mesh.get('filename'):
        origin = vis.find('origin')
        print(f"Index {i:3d}: xyz={origin.get('xyz')}, rpy={origin.get('rpy')}")
