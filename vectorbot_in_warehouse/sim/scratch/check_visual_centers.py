import re

def parse_visuals(file_path):
    with open(file_path) as f:
        content = f.read()
    
    # We want to find all <visual> blocks inside torso_link in the backup file
    torso_match = re.search(r'<link name="torso_link">(.*?)</link>', content, re.DOTALL)
    if not torso_match:
        print("torso_link not found!")
        return []
    
    torso_content = torso_match.group(1)
    visuals = re.findall(r'<visual>.*?</visual>', torso_content, re.DOTALL)
    
    parsed = []
    for vis in visuals:
        mesh_match = re.search(r'filename="[^"]*/([^"]+)"', vis)
        origin_match = re.search(r'origin xyz="([^"]+)" rpy="([^"]+)"', vis)
        if mesh_match and origin_match:
            filename = mesh_match.group(1)
            xyz = [float(x) for x in origin_match.group(1).split()]
            rpy = [float(x) for x in origin_match.group(2).split()]
            parsed.append({'filename': filename, 'xyz': xyz, 'rpy': rpy})
    return parsed

def main():
    bak2_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro.bak2'
    visuals = parse_visuals(bak2_path)
    
    left_e1_files = ["L_E1_motor_bracket.stl", "L_E1_3dp_CHP.stl", "L_E1_1_cover.stl", "L_E1_2_cover.stl"]
    right_e1_files = ["L_E1_motor_bracket.stl", "L_E1_3dp_CHP.stl", "L_E1_1_cover_Mirrored.stl", "L_E1_2_cover_Mirrored.stl"]
    
    left_e2_files = [
        "L_E2_motorholding_bracket.stl",
        "L_Wr_2_motorholding_bracket.stl",
        "L_Wr_1_motorholding_bracket.stl",
        "L_Wr_3_motorholding_bracket.stl",
        "L_Wr_motor_horn_adaptor.stl",
        "L_E2_2_cover.stl",
        "L_E2_3dp_CHP.stl",
        "ID_Needle_AXK_3047.stl",
        "ID_Thrust_51106_dummy.stl",
        "RS02.stl",
        "L_S2_M_motor_holder.stl",
        "L_E1_motor_bearing_holder.stl",
        "ID_DGBB_6200_dummy.stl"
    ]
    
    right_e2_files = [
        "L_E2_motorholding_bracket_Mirrored.stl",
        "L_Wr_2_motorholding_bracket_Mirrored.stl",
        "L_Wr_1_motorholding_bracket.stl", # Wait, is this mirrored? Let's check
        "L_Wr_3_motorholding_bracket_Mirrored.stl",
        "L_Wr_motor_horn_adaptor.stl", # Wait, is this mirrored?
        "L_E2_2_cover_Mirrored.stl",
        "L_E2_3dp_CHP_Mirrored.stl",
        "ID_Needle_AXK_3047.stl",
        "ID_Thrust_51106_dummy.stl",
        "RS02_Mirrored.stl",
        "L_S2_M_motor_holder_Mirrored.stl",
        "L_E1_motor_bearing_holder.stl",
        "ID_DGBB_6200_dummy.stl"
    ]
    
    print("--- LEFT ARM E1 PARTS ---")
    left_e1_found = []
    for vis in visuals:
        if vis['filename'] in left_e1_files and vis['xyz'][0] < 0:
            print(f"{vis['filename']}: xyz={vis['xyz']}, rpy={vis['rpy']}")
            left_e1_found.append(vis)
            
    print("\n--- RIGHT ARM E1 PARTS ---")
    right_e1_found = []
    for vis in visuals:
        if vis['filename'] in right_e1_files and vis['xyz'][0] > 0:
            print(f"{vis['filename']}: xyz={vis['xyz']}, rpy={vis['rpy']}")
            right_e1_found.append(vis)
            
    print("\n--- LEFT ARM E2 PARTS ---")
    left_e2_found = []
    for vis in visuals:
        if vis['filename'] in left_e2_files and vis['xyz'][0] < 0:
            # Filter to avoid other links
            if vis['xyz'][2] < 0.6: # E2 is lower down? Let's check
                print(f"{vis['filename']}: xyz={vis['xyz']}, rpy={vis['rpy']}")
                left_e2_found.append(vis)

    print("\n--- RIGHT ARM E2 PARTS ---")
    right_e2_found = []
    for vis in visuals:
        if vis['filename'] in right_e2_files and vis['xyz'][0] > 0:
            if vis['xyz'][2] < 0.6: # Wait, right arm E2 is mirrored, let's check its Z coordinate
                print(f"{vis['filename']}: xyz={vis['xyz']}, rpy={vis['rpy']}")
                right_e2_found.append(vis)

if __name__ == '__main__':
    main()
