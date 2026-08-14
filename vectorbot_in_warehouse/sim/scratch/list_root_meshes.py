import xml.etree.ElementTree as ET
import os

urdf_path = "/home/nihit/bots/Assembly_mass_replace/assembly_1_1/urdf/assembly_1_1.urdf"
tree = ET.parse(urdf_path)
root = tree.getroot()

# Find the 'root' link
root_link = None
for link in root.findall('link'):
    if link.get('name') == 'root':
        root_link = link
        break

if root_link is not None:
    visuals = root_link.findall('visual')
    print(f"Total visual elements in 'root' link: {len(visuals)}")
    meshes = []
    for visual in visuals:
        geom = visual.find('geometry')
        if geom is not None:
            mesh = geom.find('mesh')
            if mesh is not None:
                meshes.append(os.path.basename(mesh.get('filename')))
    # Print first 20 meshes and total count of unique meshes
    print("Unique meshes in 'root' link:")
    print(set(meshes))
else:
    print("No link named 'root' found in assembly_1_1.urdf")
