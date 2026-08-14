import re

def shift_origin(visual_block, shift):
    origin_pattern = r'<origin xyz="([^"]+)" rpy="([^"]+)"\s*/>'
    match = re.search(origin_pattern, visual_block)
    if not match:
        origin_pattern = r'<origin xyz="([^"]+)" rpy="([^"]+)"'
        match = re.search(origin_pattern, visual_block)
        
    if match:
        xyz_str = match.group(1)
        rpy_str = match.group(2)
        xyz = [float(x) for x in xyz_str.split()]
        new_xyz = [xyz[0] - shift[0], xyz[1] - shift[1], xyz[2] - shift[2]]
        new_xyz_str = f"{new_xyz[0]:.6f} {new_xyz[1]:.6f} {new_xyz[2]:.6f}"
        
        old_tag = match.group(0)
        new_tag = f'<origin xyz="{new_xyz_str}" rpy="{rpy_str}"'
        if old_tag.endswith('/>'):
            new_tag += ' />'
            
        return visual_block.replace(old_tag, new_tag)
    else:
        print("Warning: Origin tag not found in visual block:")
        print(visual_block[:100])
        return visual_block

def main():
    file_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro'
    
    with open(file_path, 'r') as f:
        content = f.read()
        
    torso_match = re.search(r'(<link name="torso_link">)(.*?)(</link>)', content, re.DOTALL)
    if not torso_match:
        print("torso_link not found!")
        return
        
    prefix = torso_match.group(1)
    torso_content = torso_match.group(2)
    suffix = torso_match.group(3)
    
    visual_blocks = re.findall(r'(<visual>.*?</visual>)', torso_content, re.DOTALL)
    print(f"Total visual blocks in torso_link: {len(visual_blocks)}")
    
    # Classify right arm visual indices:
    s1_indices = {68, 69, 70, 71}
    s2_indices = {72, 73, 74, 75, 76, 77, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110}
    e1_indices = {78, 79, 80, 81}
    e2_indices = {52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66}
    wr_indices = {82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94}
    ee_indices = {67}
    
    all_extracted = s1_indices.union(s2_indices).union(e1_indices).union(e2_indices).union(wr_indices).union(ee_indices)
    
    shift_s1 = [0.041824, 0.052366, 0.030674]
    shift_s2 = [0.064974, 0.113366, 0.030673]
    shift_e1 = [0.041824, 0.113366, -0.022327]
    shift_e2 = [0.145467, 0.072677, -0.251027]
    shift_wr = [0.182657, 0.189256, 0.371621]
    shift_ee = [0.180967, 0.167681, 0.457323]
    
    s1_visuals = []
    s2_visuals = []
    e1_visuals = []
    e2_visuals = []
    wr_visuals = []
    ee_visuals = []
    remaining_visuals = []
    
    for i, block in enumerate(visual_blocks):
        if i in s1_indices:
            s1_visuals.append(shift_origin(block, shift_s1))
        elif i in s2_indices:
            s2_visuals.append(shift_origin(block, shift_s2))
        elif i in e1_indices:
            e1_visuals.append(shift_origin(block, shift_e1))
        elif i in e2_indices:
            e2_visuals.append(shift_origin(block, shift_e2))
        elif i in wr_indices:
            wr_visuals.append(shift_origin(block, shift_wr))
        elif i in ee_indices:
            ee_visuals.append(shift_origin(block, shift_ee))
        else:
            remaining_visuals.append(block)
            
    print(f"Extracted S1 visuals: {len(s1_visuals)}")
    print(f"Extracted S2 visuals: {len(s2_visuals)}")
    print(f"Extracted E1 visuals: {len(e1_visuals)}")
    print(f"Extracted E2 visuals: {len(e2_visuals)}")
    print(f"Extracted Wr visuals: {len(wr_visuals)}")
    print(f"Extracted EE visuals: {len(ee_visuals)}")
    print(f"Remaining visuals in torso_link: {len(remaining_visuals)}")
    
    inertial_col_content = torso_content
    for block in visual_blocks:
        inertial_col_content = inertial_col_content.replace(block, '', 1)
        
    inertial_col_content = "\n".join([line for line in inertial_col_content.splitlines() if line.strip()])
    new_torso_content = inertial_col_content + "\n" + "\n".join(remaining_visuals) + "\n"
    
    inertial_template = """        <inertial>
            <mass value="2.0" />
            <origin xyz="0 0 0" rpy="0 0 0" />
            <inertia ixx="0.05" ixy="0.0" ixz="0.0" iyy="0.05" iyz="0.0" izz="0.05" />
        </inertial>"""
        
    # Generate Link definitions
    right_shoulder_link_1_str = f"""    <link name="right_shoulder_link_1">
{inertial_template}
{"".join(s1_visuals)}
    </link>"""

    right_shoulder_link_2_str = f"""    <link name="right_shoulder_link_2">
{inertial_template}
{"".join(s2_visuals)}
    </link>"""

    right_elbow_link_1_str = f"""    <link name="right_elbow_link_1">
{inertial_template}
{"".join(e1_visuals)}
    </link>"""

    right_elbow_link_2_str = f"""    <link name="right_elbow_link_2">
{inertial_template}
{"".join(e2_visuals)}
    </link>"""

    wrist_link_1_str = f"""    <link name="wrist_link_1">
{inertial_template}
{"".join(wr_visuals)}
    </link>"""

    ee_link_str = f"""    <link name="ee_link">
{inertial_template}
{"".join(ee_visuals)}
    </link>"""

    # Generate Joint definitions
    right_shoulder_1_str = """    <joint name="right_shoulder_1" type="revolute">
        <origin xyz="0.041824 0.052366 0.030674" rpy="0 0 0" />
        <axis xyz="0 1 0" />
        <parent link="torso_link" />
        <child link="right_shoulder_link_1" />
        <limit lower="-1.5708" upper="1.5708" effort="200.0" velocity="3.0" />
    </joint>"""

    right_shoulder_2_str = """    <joint name="right_shoulder_2" type="revolute">
        <origin xyz="0.023150 0.061000 -0.000001" rpy="0 0 0" />
        <axis xyz="1 0 0" />
        <parent link="right_shoulder_link_1" />
        <child link="right_shoulder_link_2" />
        <limit lower="-1.5708" upper="1.5708" effort="200.0" velocity="3.0" />
    </joint>"""

    right_bicep_str = """    <joint name="right_bicep" type="revolute">
        <origin xyz="-0.023150 0.000000 -0.053000" rpy="0 0 0" />
        <axis xyz="0 0 1" />
        <parent link="right_shoulder_link_2" />
        <child link="right_elbow_link_1" />
        <limit lower="-1.5708" upper="1.5708" effort="200.0" velocity="3.0" />
    </joint>"""

    right_forearm_str = """    <joint name="right_forearm" type="revolute">
        <origin xyz="0.103643 -0.040689 -0.228700" rpy="0 0 0" />
        <axis xyz="0 1 0" />
        <parent link="right_elbow_link_1" />
        <child link="right_elbow_link_2" />
        <limit lower="-1.5708" upper="1.5708" effort="200.0" velocity="3.0" />
    </joint>"""

    right_wrist_1_str = """    <joint name="right_wrist_1" type="revolute">
        <origin xyz="0.037190 0.116579 0.622648" rpy="0 0 0" />
        <axis xyz="0 0 1" />
        <parent link="right_elbow_link_2" />
        <child link="wrist_link_1" />
        <limit lower="-1.5708" upper="1.5708" effort="100.0" velocity="100.0" />
    </joint>"""

    right_wrist_2_str = """    <joint name="right_wrist_2" type="revolute">
        <origin xyz="-0.001689 -0.021575 0.085702" rpy="0 0 0" />
        <axis xyz="0 1 0" />
        <parent link="wrist_link_1" />
        <child link="ee_link" />
        <limit lower="-1.5708" upper="1.5708" effort="100.0" velocity="100.0" />
    </joint>"""

    # Reconstruct torso_link in the XML content
    new_torso_link_str = f'<link name="torso_link">\n{new_torso_content}</link>\n'
    updated_content = content.replace(torso_match.group(0), new_torso_link_str)
    
    # We will insert the new links and joints after left_forearm joint
    left_forearm_match = re.search(r'(<joint name="left_forearm" type="revolute">.*?</joint>)', updated_content, re.DOTALL)
    if not left_forearm_match:
        print("left_forearm joint not found in updated content!")
        return
        
    insert_str = "\n".join([
        left_forearm_match.group(1),
        "",
        "    <!-- Right Arm Kinematic Chain -->",
        right_shoulder_link_1_str,
        right_shoulder_1_str,
        "",
        right_shoulder_link_2_str,
        right_shoulder_2_str,
        "",
        right_elbow_link_1_str,
        right_bicep_str,
        "",
        right_elbow_link_2_str,
        right_forearm_str,
        "",
        wrist_link_1_str,
        right_wrist_1_str,
        "",
        ee_link_str,
        right_wrist_2_str
    ])
    
    updated_content = updated_content.replace(left_forearm_match.group(1), insert_str)
    
    with open(file_path, 'w') as f:
        f.write(updated_content)
        
    print("vector.xacro successfully refactored and right arm integrated!")

if __name__ == '__main__':
    main()
