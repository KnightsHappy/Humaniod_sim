import re
import xml.etree.ElementTree as ET

color_map = {
    'base_link': 'white',
    'rear_caster_visual': 'dark_grey',
    'front_caster_visual': 'dark_grey',
    'slider_1': 'dark_grey',
    'torso_1': 'white',
    'left_arm_link_1_1': 'white',
    'left_shoulder_1': 'white',
    'left_bicep_1': 'white',
    'left_forearm_v2_1': 'white',
    'right_arm_link_1_1': 'white',
    'right_shoulder_1': 'white',
    'right_bicep_1': 'white',
    'right_forearm_v1_1': 'white',
    'neck_v2_1': 'black',
    'head_v1_1': 'white',
    'right_wheel_1': 'black',
    'left_wheel_1': 'black',
    'camera_1': 'black',
    'left_hand_palm_1': 'white',
    'left_hand_finger_1': 'dark_grey',
    'right_hand_palm_1': 'white',
    'right_hand_finger_1': 'dark_grey'
}

file_path = '/home/karan/vectorbots/sim/vector_description/urdf/vector.xacro'
tree = ET.parse(file_path)
root = tree.getroot()

for link in root.findall('link'):
    link_name = link.get('name')
    for visual in link.findall('visual'):
        vis_name = visual.get('name')
        
        target_name = vis_name if vis_name and vis_name in color_map else link_name
        
        if target_name in color_map:
            new_color = color_map[target_name]
            mat = visual.find('material')
            if mat is not None:
                mat.set('name', new_color)

tree.write(file_path, xml_declaration=True, encoding='utf-8')
