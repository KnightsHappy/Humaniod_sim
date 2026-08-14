xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"

with open(xacro_path, 'r') as f:
    lines = f.readlines()

def find_inertial_block(link_name):
    # Find the line with <link name="link_name">
    link_idx = -1
    for idx, line in enumerate(lines):
        if f'link name="{link_name}"' in line or f"link name='{link_name}'" in line:
            link_idx = idx
            break
    
    if link_idx == -1:
        print(f"Could not find link {link_name}")
        return
    
    # Find <inertial> after link_idx
    inertial_start = -1
    inertial_end = -1
    for idx in range(link_idx, len(lines)):
        if '<inertial>' in lines[idx]:
            inertial_start = idx
            break
            
    if inertial_start != -1:
        for idx in range(inertial_start, len(lines)):
            if '</inertial>' in lines[idx]:
                inertial_end = idx
                break
                
    if inertial_start != -1 and inertial_end != -1:
        print(f"Link: {link_name}")
        print(f"  Link tag line: {link_idx + 1}")
        print(f"  Inertial block lines: {inertial_start + 1} to {inertial_end + 1}")
        for i in range(inertial_start, inertial_end + 1):
            print(f"    {i+1}: {lines[i]}", end='')
        print("-" * 40)

find_inertial_block('shoulder_link_1_link')
find_inertial_block('right_shoulder_link_1')
find_inertial_block('shoulder_link_2')
find_inertial_block('right_shoulder_link_2')
