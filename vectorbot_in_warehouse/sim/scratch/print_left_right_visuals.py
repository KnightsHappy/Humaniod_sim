import xml.etree.ElementTree as ET
import os

def main():
    file_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro.bak2'
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # 1. Gather left arm link visuals
    left_links = ['shoulder_link_1_link', 'shoulder_link_2', 'elbow_link_1', 'elbow_link_2']
    left_visuals = {}
    for lname in left_links:
        link = next((l for l in root.findall('link') if l.get('name') == lname), None)
        if link is not None:
            left_visuals[lname] = []
            for vis in link.findall('visual'):
                mesh = vis.find('geometry').find('mesh')
                origin = vis.find('origin')
                if mesh is not None and origin is not None:
                    mesh_name = os.path.basename(mesh.get('filename'))
                    xyz = [float(x) for x in origin.get('xyz').split()]
                    rpy = [float(x) for x in origin.get('rpy').split()]
                    left_visuals[lname].append({'mesh': mesh_name, 'xyz': xyz, 'rpy': rpy})

    # 2. Gather torso_link visuals (which contain the right arm visuals before refactoring)
    torso_link = next((l for l in root.findall('link') if l.get('name') == 'torso_link'), None)
    torso_visuals = []
    if torso_link is not None:
        for vis in torso_link.findall('visual'):
            mesh = vis.find('geometry').find('mesh')
            origin = vis.find('origin')
            if mesh is not None and origin is not None:
                mesh_name = os.path.basename(mesh.get('filename'))
                xyz = [float(x) for x in origin.get('xyz').split()]
                rpy = [float(x) for x in origin.get('rpy').split()]
                torso_visuals.append({'mesh': mesh_name, 'xyz': xyz, 'rpy': rpy})

    print("=== LEFT ARM VISUALS IN LINKS ===")
    for lname, visuals in left_visuals.items():
        print(f"\nLink: {lname}")
        for vis in visuals:
            print(f"  {vis['mesh']}: xyz={vis['xyz']}, rpy={vis['rpy']}")

    print("\n=== RIGHT ARM VISUALS IN TORSO ===")
    # Print the right arm visuals (typically containing Mirrored in filename or have positive X coordinates)
    right_keywords = ['Mirrored', 'R_Hand', 'Part_3_5', 'eBom_FreeParts', 'Wheel_25kg', 'Wheel_gear_25kg', 'Part_3_Mirrored_Mirrored']
    for vis in torso_visuals:
        # Check if it matches right arm keywords or is on the right side (positive X)
        is_right = False
        if any(kw in vis['mesh'] for kw in right_keywords):
            is_right = True
        elif vis['xyz'][0] > 0:
            is_right = True
            
        if is_right:
            print(f"  {vis['mesh']}: xyz={vis['xyz']}, rpy={vis['rpy']}")

if __name__ == '__main__':
    main()
