import re
import xml.etree.ElementTree as ET

def main():
    file_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro'
    with open(file_path, 'r') as f:
        content = f.read()

    # Find torso_link definition
    torso_match = re.search(r'<link name="torso_link">(.*?)</link>', content, re.DOTALL)
    if not torso_match:
        print("torso_link not found!")
        return

    torso_content = torso_match.group(1)
    # Extract all visual blocks
    visual_blocks = re.findall(r'(<visual>.*?</visual>)', torso_content, re.DOTALL)
    print(f"Total visual blocks in torso_link: {len(visual_blocks)}")

    # We want to classify all right arm visual blocks:
    # 1) R-S1 (right_shoulder_link_1)
    # 2) R-S2 (right_shoulder_link_2)
    # 3) R-E1 (right_elbow_link_1)
    # 4) R-E2 (right_elbow_link_2)
    # 5) R-Wr (wrist_link_1)
    # 6) R-Hand-EE (ee_link)

    # Let's map mesh filenames to links based on Onshape hierarchy
    # (Checking suffixes/mirrored status)
    
    # We can do this by inspecting each visual's mesh filename
    categorized = {
        'R-S1': [],
        'R-S2': [],
        'R-E1': [],
        'R-E2': [],
        'R-Wr': [],
        'R-Hand-EE': [],
        'remaining': []
    }

    # S1 keywords:
    s1_meshes = {'L_B_S2_cover_Mirrored.stl', 'L_S2_3dprinted_CHP.stl', 'L_A_S2_cover_Mirrored.stl', 'L_S2_bracket.stl'}
    # Note: L_S2_bracket.stl and L_S2_3dprinted_CHP.stl also exist in left arm shoulder_link_1_link.
    # However, in torso_link, only the right arm versions are left! (Left arm ones were already extracted).
    # So we can match them if they are in the range of S1.
    
    # Let's inspect the indices of these matches to make sure they are correct.
    for i, block in enumerate(visual_blocks):
        mesh_match = re.search(r'mesh filename="file://\$\(find vector_description\)/meshes/([^"]+)"', block)
        if not mesh_match:
            categorized['remaining'].append((i, block, "No mesh"))
            continue
        mesh_name = mesh_match.group(1)
        
        # Check by index or mesh filename
        # Let's define index-based classification to be 100% precise:
        # S1: index 3202 to 3241 in line numbers, which correspond to indices in visual_blocks:
        # Let's find index by printing them out first!
        categorized['remaining'].append((i, block, mesh_name))

    # Let's search for right arm meshes in the list and print them
    right_keywords = ['mirrored', 'r_hand_ee', 'l_s1_motor_bearing_adaptor', 'l_s2_bracket', 'l_s2_3dprinted_chp', 'l_e1_motor_bracket', 'l_e1_3dp_chp', 'l_wr_1_motorholding_bracket', 'l_wr_motor_horn_adaptor', 'wheel_v5', 'wheel_gear_v6', '_6mm_bearing_v2', 'rds5160_v39', 'rds3235_gear']
    
    right_arm_indices = []
    print("\nRight Arm Visual Blocks in torso_link:")
    for idx, block, mesh in categorized['remaining']:
        is_right = False
        for kw in right_keywords:
            if kw in mesh.lower():
                is_right = True
                break
        if is_right:
            print(f"Index {idx:3d}: {mesh}")
            right_arm_indices.append(idx)

if __name__ == '__main__':
    main()
