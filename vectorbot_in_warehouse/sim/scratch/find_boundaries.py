import xml.etree.ElementTree as ET

tree = ET.parse('/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro')
root = tree.getroot()

root_link = next(l for l in root.findall('link') if l.get('name') == 'root')
visuals = root_link.findall('visual')

# Print out a comprehensive list of all visuals in root
with open('/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/visual_list.txt', 'w') as f:
    for i, vis in enumerate(visuals):
        mesh = vis.find('geometry').find('mesh')
        filename = mesh.get('filename') if mesh is not None else "None"
        f.write(f"{i:3d}: {filename}\n")

print(f"Total visuals: {len(visuals)}")
