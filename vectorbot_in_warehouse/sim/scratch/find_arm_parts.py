import re

def main():
    file_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro'
    
    with open(file_path, 'r') as f:
        content = f.read()
        
    # Let's find torso_link block
    torso_match = re.search(r'<link name="torso_link">(.*?)</link>', content, re.DOTALL)
    if not torso_match:
        print("torso_link not found!")
        return
        
    torso_content = torso_match.group(1)
    
    # Let's split torso_content into visual blocks
    visual_blocks = re.findall(r'(<visual>.*?</visual>)', torso_content, re.DOTALL)
    print(f"Found {len(visual_blocks)} visual blocks in torso_link")
    
    # We want to identify blocks containing meshes from:
    # 1) S2<1> subassembly parts:
    s2_keywords = [
        "L_E1_2_motor_bracket",
        "L_S1_Motor_bearing_Adaptor",
        "L_S2_Motor_supporting_bracket",
        "L_upperarm_front_support_bracket",
        "ID_Needle_AXK_3047",
        "RS02",
        "L_S2_A_cover",
        "L1_upperarm_AL_ext",
        "L_S2_B_cover",
        "L_E1_1_motorbracket",
        "ID_DGBB_6200_dummy",
        "L_upperarm_back_support_bracket",
        "ID_Thrust_51206_dummy",
        "L_S2_M_motor_holder",
        "L_S2_Rbearing_Holder"
    ]
    
    # 2) shoulder1_to_shoulder2<1> subassembly parts (elbow_link_1):
    elbow1_keywords = [
        "L_E1_1_cover",
        "L_E1_motor_bracket",
        "L_E1_3dp_CHP",
        "L_E1_2_cover"
    ]
    
    # 3) E2<1> subassembly parts (elbow_link_2):
    elbow2_keywords = [
        "L_E2_1_cover",
        "L_E2_motorholding_bracket",
        "L_Wr_2_motorholding_bracket",
        "L_Wr_1_motorholding_bracket",
        "L_Wr_3_motorholding_bracket",
        "L_Wr_motor_horn_adaptor",
        "L_E2_2_cover",
        "L_E2_3dp_CHP",
        # Wait, what about other parts under E2<1> in Onshape structure? Let's check:
        # ID-Thrust-51106-dummy, RS02, ID-DGBB-6200-dummy, ID-Needle-AXK-3047, L-S2-M-motor-holder etc.
        # But wait! Let's check which ones are present in the URDF torso_link!
        "L_E2_1_cover",
        "L_E2_motorholding_bracket",
        "L_Wr_2_motorholding_bracket",
        "L_Wr_1_motorholding_bracket",
        "L_Wr_3_motorholding_bracket",
        "L_Wr_motor_horn_adaptor",
        "L_E2_2_cover",
        "L_E2_3dp_CHP"
    ]
    
    def match_keywords(block, keywords):
        for kw in keywords:
            # Match word boundaries or filenames
            if kw in block:
                # Exclude mirrored/rightarm variants if they are named differently (e.g. contain "Mirrored")
                if "Mirrored" in block and "Mirrored" not in kw:
                    continue
                return kw
        return None
        
    print("\n--- S2 <1> parts ---")
    for i, block in enumerate(visual_blocks):
        kw = match_keywords(block, s2_keywords)
        if kw:
            origin = re.search(r'origin xyz="([^"]+)"', block)
            origin_str = origin.group(1) if origin else "None"
            print(f"Index {i}: {kw} | Origin: {origin_str}")
            
    print("\n--- shoulder1_to_shoulder2 <1> parts ---")
    for i, block in enumerate(visual_blocks):
        kw = match_keywords(block, elbow1_keywords)
        if kw:
            origin = re.search(r'origin xyz="([^"]+)"', block)
            origin_str = origin.group(1) if origin else "None"
            print(f"Index {i}: {kw} | Origin: {origin_str}")
            
    print("\n--- E2 <1> parts ---")
    for i, block in enumerate(visual_blocks):
        kw = match_keywords(block, elbow2_keywords)
        if kw:
            origin = re.search(r'origin xyz="([^"]+)"', block)
            origin_str = origin.group(1) if origin else "None"
            print(f"Index {i}: {kw} | Origin: {origin_str}")

if __name__ == '__main__':
    main()
