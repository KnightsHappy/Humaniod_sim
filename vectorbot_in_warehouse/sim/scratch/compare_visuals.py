import xml.etree.ElementTree as ET

xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"
tree = ET.parse(xacro_path)
root = tree.getroot()

def print_link_visuals(link_name):
    print(f"\n--- Visuals for {link_name} ---")
    for elem in root.findall('.//link'):
        if elem.get('name') == link_name:
            for visual in elem.findall('visual'):
                origin = visual.find('origin')
                xyz = origin.get('xyz') if origin is not None else "0 0 0"
                rpy = origin.get('rpy') if origin is not None else "0 0 0"
                mesh = visual.find('.//mesh')
                mesh_fn = mesh.get('filename') if mesh is not None else "none"
                print(f"Mesh: {mesh_fn}")
                print(f"  xyz: {xyz}, rpy: {rpy}")

print_link_visuals('shoulder_link_1_link')
print_link_visuals('right_shoulder_link_1')
