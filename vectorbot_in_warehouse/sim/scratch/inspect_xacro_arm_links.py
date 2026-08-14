import xml.etree.ElementTree as ET

xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"
tree = ET.parse(xacro_path)
root = tree.getroot()

def inspect_link(link_name):
    print(f"\nLink: {link_name}")
    for elem in root.findall('.//link'):
        if elem.get('name') == link_name:
            inertial = elem.find('inertial')
            if inertial is not None:
                mass = inertial.find('mass').get('value')
                origin = inertial.find('origin')
                xyz = origin.get('xyz') if origin is not None else "0 0 0"
                print(f"  Mass: {mass} | Origin: {xyz}")
            
            meshes = []
            for visual in elem.findall('visual'):
                mesh = visual.find('.//mesh')
                if mesh is not None:
                    meshes.append(mesh.get('filename').split('/')[-1])
            print(f"  Meshes ({len(meshes)}): {meshes}")

inspect_link('shoulder_link_1_link')
inspect_link('shoulder_link_2')
inspect_link('elbow_link_1')
inspect_link('elbow_link_2')
inspect_link('right_shoulder_link_1')
inspect_link('right_shoulder_link_2')
inspect_link('right_elbow_link_1')
inspect_link('right_elbow_link_2')
inspect_link('wrist_link_1')
inspect_link('ee_link')
