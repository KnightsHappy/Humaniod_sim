import re
import os

def shift_origin(visual_block, shift):
    # Search for the origin tag: <origin xyz="..." rpy="..." />
    origin_pattern = r'<origin xyz="([^"]+)" rpy="([^"]+)"\s*/>'
    match = re.search(origin_pattern, visual_block)
    if not match:
        # Try without trailing slash or different spacing
        origin_pattern = r'<origin xyz="([^"]+)" rpy="([^"]+)"'
        match = re.search(origin_pattern, visual_block)
        
    if match:
        xyz_str = match.group(1)
        rpy_str = match.group(2)
        xyz = [float(x) for x in xyz_str.split()]
        new_xyz = [xyz[0] - shift[0], xyz[1] - shift[1], xyz[2] - shift[2]]
        new_xyz_str = f"{new_xyz[0]:.6f} {new_xyz[1]:.6f} {new_xyz[2]:.6f}"
        
        # Replace only the xyz part in the origin tag
        old_tag = match.group(0)
        new_tag = f'<origin xyz="{new_xyz_str}" rpy="{rpy_str}"'
        if old_tag.endswith('/>'):
            new_tag += ' />'
        
        updated_block = visual_block.replace(old_tag, new_tag)
        return updated_block
    else:
        print("Warning: Origin tag not found in visual block:")
        print(visual_block[:100])
        return visual_block

def main():
    file_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro'
    
    with open(file_path, 'r') as f:
        content = f.read()
        
    # Find torso_link definition
    torso_match = re.search(r'(<link name="torso_link">)(.*?)(</link>)', content, re.DOTALL)
    if not torso_match:
        print("torso_link not found!")
        return
        
    prefix = torso_match.group(1)
    torso_content = torso_match.group(2)
    suffix = torso_match.group(3)
    
    # We must find the visual blocks inside torso_link
    # A visual block starts with <visual> and ends with </visual>
    visual_blocks = re.findall(r'(<visual>.*?</visual>)', torso_content, re.DOTALL)
    print(f"Total visual blocks in torso_link: {len(visual_blocks)}")
    
    # Let's define the indices we want to extract (0-indexed)
    s2_indices = {112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 162, 163, 164, 165}
    e1_indices = {156, 157, 158, 159}
    e2_indices = {128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142}
    
    all_extracted = s2_indices.union(e1_indices).union(e2_indices)
    
    s2_shifts = [-0.295326, 0.113366, 0.030673]
    e1_shifts = [-0.272176, 0.113366, -0.022327]
    e2_shifts = [-0.250593, 0.082666, -0.255727]
    
    s2_visuals = []
    e1_visuals = []
    e2_visuals = []
    remaining_visuals = []
    
    for i, block in enumerate(visual_blocks):
        if i in s2_indices:
            s2_visuals.append(shift_origin(block, s2_shifts))
        elif i in e1_indices:
            e1_visuals.append(shift_origin(block, e1_shifts))
        elif i in e2_indices:
            e2_visuals.append(shift_origin(block, e2_shifts))
        else:
            remaining_visuals.append(block)
            
    print(f"Extracted S2 visuals: {len(s2_visuals)}")
    print(f"Extracted E1 visuals: {len(e1_visuals)}")
    print(f"Extracted E2 visuals: {len(e2_visuals)}")
    print(f"Remaining visuals in torso_link: {len(remaining_visuals)}")
    
    # Reconstruct torso_link body (inertial, collision, remaining visuals)
    # Let's find torso_link's inertial and collision blocks
    # We can do this by removing all visual blocks from torso_content, then putting remaining_visuals back.
    inertial_col_content = torso_content
    for block in visual_blocks:
        inertial_col_content = inertial_col_content.replace(block, '', 1)
        
    # Now build new torso_link content
    # Clean up empty lines/spaces from inertial_col_content
    inertial_col_content = "\n".join([line for line in inertial_col_content.splitlines() if line.strip()])
    
    new_torso_content = inertial_col_content + "\n" + "\n".join(remaining_visuals) + "\n"
    
    # Let's build the new links strings
    inertial_template = """        <inertial>
            <mass value="2.0" />
            <origin xyz="0 0 0" rpy="0 0 0" />
            <inertia ixx="0.05" ixy="0.0" ixz="0.0" iyy="0.05" iyz="0.0" izz="0.05" />
        </inertial>"""
        
    shoulder_link_2_str = f"""    <link name="shoulder_link_2">
{inertial_template}
{"".join(s2_visuals)}
    </link>"""

    elbow_link_1_str = f"""    <link name="elbow_link_1">
{inertial_template}
{"".join(e1_visuals)}
    </link>"""

    elbow_link_2_str = f"""    <link name="elbow_link_2">
{inertial_template}
{"".join(e2_visuals)}
    </link>"""

    # Let's build the new joints strings
    left_shoulder_joint_str = """    <joint name="left_shoulder" type="revolute">
        <origin xyz="-0.02315 0.061 0.0" rpy="0 0 0" />
        <axis xyz="1 0 0" />
        <parent link="shoulder_link_1_link" />
        <child link="shoulder_link_2" />
        <limit lower="-1.5708" upper="1.5708" effort="200.0" velocity="3.0" />
    </joint>"""

    left_bicep_joint_str = """    <joint name="left_bicep" type="revolute">
        <origin xyz="0.02315 0.0 -0.053" rpy="0 0 0" />
        <axis xyz="0 0 1" />
        <parent link="shoulder_link_2" />
        <child link="elbow_link_1" />
        <limit lower="-1.5708" upper="1.5708" effort="200.0" velocity="3.0" />
    </joint>"""

    left_forearm_joint_str = """    <joint name="left_forearm" type="revolute">
        <origin xyz="0.021583 -0.0307 -0.2334" rpy="0 0 0" />
        <axis xyz="0 1 0" />
        <parent link="elbow_link_1" />
        <child link="elbow_link_2" />
        <limit lower="-1.5708" upper="1.5708" effort="200.0" velocity="3.0" />
    </joint>"""

    # Construct the entire replacement for torso_link
    new_torso_link_str = f'<link name="torso_link">\n{new_torso_content}</link>\n'
    
    # We will replace the old torso_link with the new torso_link
    updated_content = content.replace(torso_match.group(0), new_torso_link_str)
    
    # Now we insert the new links and joints. Let's find where to insert them.
    # We can insert them right after shoulder_link_1 joint.
    shoulder_joint_match = re.search(r'(<joint name="shoulder_link_1" type="revolute">.*?</joint>)', updated_content, re.DOTALL)
    if not shoulder_joint_match:
        print("shoulder_link_1 joint not found!")
        return
        
    joint_insert_str = "\n".join([
        shoulder_joint_match.group(1),
        "",
        shoulder_link_2_str,
        left_shoulder_joint_str,
        "",
        elbow_link_1_str,
        left_bicep_joint_str,
        "",
        elbow_link_2_str,
        left_forearm_joint_str
    ])
    
    updated_content = updated_content.replace(shoulder_joint_match.group(1), joint_insert_str)
    
    # Write to file
    with open(file_path, 'w') as f:
        f.write(updated_content)
        
    print("vector.xacro successfully refactored!")

if __name__ == '__main__':
    main()
