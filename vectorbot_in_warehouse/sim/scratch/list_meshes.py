import xml.etree.ElementTree as ET

tree = ET.parse('/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro')
root = tree.getroot()

# Find the 'root' link
root_link = None
for link in root.findall('link'):
    if link.get('name') == 'root':
        root_link = link
        break

if root_link is not None:
    visuals = root_link.findall('visual')
    print(f"Total visuals in root link: {len(visuals)}")
    
    # Print the first 20 and last 20 mesh filenames
    for i, vis in enumerate(visuals):
        geom = vis.find('geometry')
        if geom is not None:
            mesh = geom.find('mesh')
            if mesh is not None:
                filename = mesh.get('filename')
                print(f"{i:3d}: {filename}")
else:
    print("Could not find root link")
