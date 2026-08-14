import xml.etree.ElementTree as ET

xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"
tree = ET.parse(xacro_path)
root = tree.getroot()

print("Joints in vector.xacro:")
for joint in root.findall('.//joint'):
    name = joint.get('name')
    parent = joint.find('parent').get('link')
    child = joint.find('child').get('link')
    
    # Filter for arm joints
    if 'shoulder' in name or 'elbow' in name or 'wrist' in name or 'ee' in name or 'left_arm' in name or 'right_arm' in name or 'hand' in name or child in ['shoulder_link_1_link', 'shoulder_link_2', 'elbow_link_1', 'elbow_link_2', 'right_shoulder_link_1', 'right_shoulder_link_2', 'right_elbow_link_1', 'right_elbow_link_2', 'wrist_link_1', 'ee_link']:
        origin = joint.find('origin')
        xyz = origin.get('xyz') if origin is not None else "0 0 0"
        rpy = origin.get('rpy') if origin is not None else "0 0 0"
        print(f"Joint: {name:25} | Parent: {parent:25} | Child: {child:25} | XYZ: {xyz:30} | RPY: {rpy}")
