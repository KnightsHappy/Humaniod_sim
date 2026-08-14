import xml.etree.ElementTree as ET
import os

urdf_path = "/home/nihit/bots/Assembly_mass_replace/assembly_1_1/urdf/assembly_1_1.urdf"
xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"

# Parse URDF and get links/meshes
tree_urdf = ET.parse(urdf_path)
root_urdf = tree_urdf.getroot()

urdf_meshes = {}
for link in root_urdf.findall('link'):
    name = link.get('name')
    if name == 'root':
        continue
    inertial = link.find('inertial')
    if inertial is not None:
        meshes = []
        for visual in link.findall('visual'):
            geom = visual.find('geometry')
            if geom is not None:
                mesh = geom.find('mesh')
                if mesh is not None:
                    meshes.append(os.path.basename(mesh.get('filename')))
        urdf_meshes[name] = meshes

# Parse XACRO
tree_xacro = ET.parse(xacro_path)
root_xacro = tree_xacro.getroot()

print("Mapping from URDF mesh to Xacro link:")
for urdf_link_name, meshes in urdf_meshes.items():
    print(f"\nURDF Link: {urdf_link_name} (Meshes: {meshes})")
    for mesh_name in meshes:
        # Find which link in xacro contains this mesh
        found_links = []
        for elem in root_xacro.iter():
            if elem.tag == 'link' or elem.tag.endswith('link'):
                xacro_link_name = elem.get('name')
                for m in elem.findall('.//mesh'):
                    fn = m.get('filename')
                    if fn and os.path.basename(fn) == mesh_name:
                        found_links.append(xacro_link_name)
        print(f"  Mesh {mesh_name} found in Xacro link(s): {found_links}")
