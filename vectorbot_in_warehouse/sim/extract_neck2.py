#!/usr/bin/env python3
"""Extract WEBCAM-Final-Assembly-Neck-Mechanism visuals from torso_link
into a new neck_link_2 and add a revolute joint from neck_link_1 to neck_link_2."""

import re

XACRO_PATH = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"

# Mesh filenames (basename patterns) that belong to WEBCAM-Final-Assembly-Neck-Mechanism
WEBCAM_MESHES = {
    "eBom_FreeParts.stl",
    "eBom_FreeParts_1.stl",
    "eBom_FreeParts_2.stl",
    "eBom_FreeParts_3.stl",
    "eBom_FreeParts_4.stl",
    "eBom_FreeParts_5.stl",
    "Wheel_25kg.stl",
    "Wheel_25kg_1.stl",
    "_93475A210.stl",
    "_93475A210_1.stl",
    "Gear__25R_0_00_.stl",
    "Gear__25R_0_00__1.stl",
    "Wheel_gear_25kg.stl",
    "Wheel_gear_25kg_1.stl",
    "Neck_motor_cover_B.stl",
    "Neck_motor_support_3dprinted.stl",
    "Camera_B_cross_piece.stl",
    "Camera_A_Cross_piece.stl",
    "Neck_Motor_cover_A.stl",
    "Camera_mount.stl",
}

with open(XACRO_PATH, "r") as f:
    lines = f.readlines()

# --- Step 1: Find all <visual>...</visual> blocks inside torso_link that contain WEBCAM meshes ---
# torso_link starts at line 2466 (0-indexed: 2465) and </link> at line 3496 (0-indexed: 3495)
torso_start = None
torso_end = None
for i, line in enumerate(lines):
    if '<link name="torso_link">' in line:
        torso_start = i
    # Find the </link> that closes torso_link
    if torso_start is not None and torso_end is None and '</link>' in line and i > torso_start + 10:
        torso_end = i
        break

print(f"torso_link: lines {torso_start+1} to {torso_end+1}")

# Parse visual blocks within torso_link
visual_blocks = []  # list of (start_idx, end_idx, is_webcam, content)
i = torso_start
while i <= torso_end:
    line = lines[i]
    # Check for <visual> tag (may have leading whitespace)
    if '<visual>' in line and '</visual>' not in line:
        block_start = i
        # Find closing </visual>
        j = i + 1
        while j <= torso_end:
            if '</visual>' in lines[j]:
                block_end = j
                break
            j += 1
        else:
            i += 1
            continue
        
        # Check if this visual block contains a WEBCAM mesh
        block_content = ''.join(lines[block_start:block_end+1])
        is_webcam = False
        for mesh_name in WEBCAM_MESHES:
            if mesh_name in block_content:
                is_webcam = True
                break
        
        visual_blocks.append((block_start, block_end, is_webcam, block_content))
        i = block_end + 1
    else:
        i += 1

webcam_blocks = [(s, e, c) for s, e, is_w, c in visual_blocks if is_w]
non_webcam_blocks = [(s, e) for s, e, is_w, c in visual_blocks if not is_w]

print(f"Total visual blocks in torso_link: {len(visual_blocks)}")
print(f"WEBCAM visual blocks to extract: {len(webcam_blocks)}")
print(f"Non-WEBCAM visual blocks to keep: {len(non_webcam_blocks)}")

# Print WEBCAM blocks with their mesh names for verification
for s, e, content in webcam_blocks:
    mesh_match = re.search(r'meshes/([^"]+)"', content)
    mesh_name = mesh_match.group(1) if mesh_match else "unknown"
    print(f"  Lines {s+1}-{e+1}: {mesh_name}")

# --- Step 2: Build the new file content ---
# Collect lines to remove (WEBCAM visual blocks from torso_link)
lines_to_remove = set()
for s, e, _ in webcam_blocks:
    for idx in range(s, e + 1):
        lines_to_remove.add(idx)

# Build extracted visual content for neck_link_2
extracted_visuals = []
for s, e, content in webcam_blocks:
    extracted_visuals.append(content)

# Create the neck_link_2 definition and joint
# The joint origin should be at the position where neck_link_1 connects.
# neck_link_1 is at the neck bracket position. The WEBCAM mechanism sits on top.
# Using the Wheel_25kg<1> position as reference: xyz="-0.115326 0.055066 0.049673"
# The torso_to_neck_1_joint origin is: xyz="-0.115176 0.058366 0.108173"
# So neck_link_2 joint should be relative to neck_link_1's frame.

neck_link_2_def = """
    <!-- neck_link_2: WEBCAM-Final-Assembly-Neck-Mechanism parts split from torso_link -->
    <link name="neck_link_2">
        <inertial>
            <mass value="0.25" />
            <origin xyz="0 0 0" rpy="0 0 0" />
            <inertia ixx="2.0e-04" ixy="0.0" ixz="0.0" iyy="2.0e-04" iyz="0.0" izz="2.0e-04" />
        </inertial>
"""

for visual_content in extracted_visuals:
    neck_link_2_def += visual_content

neck_link_2_def += """    </link>

    <joint name="neck_1_to_neck_2_joint" type="revolute">
        <origin xyz="0 0 0" rpy="0 0 0" />
        <axis xyz="0 1 0" />
        <parent link="neck_link_1" />
        <child link="neck_link_2" />
        <limit lower="-0.7854" upper="0.7854" effort="30.0" velocity="2.0" />
    </joint>

"""

# --- Step 3: Assemble the new file ---
new_lines = []
for i, line in enumerate(lines):
    if i in lines_to_remove:
        continue
    new_lines.append(line)
    # After the torso_to_neck_1_joint closing tag (</joint> at original line 3533),
    # insert the neck_link_2 definition
    # But we need to find this after removal... let's insert after </joint> for torso_to_neck_1_joint
    if '</joint>' in line:
        # Check if the preceding lines contain torso_to_neck_1_joint
        context = ''.join(lines[max(0, i-6):i+1])
        if 'torso_to_neck_1_joint' in context:
            new_lines.append(neck_link_2_def)

with open(XACRO_PATH, "w") as f:
    f.writelines(new_lines)

print(f"\nDone! Extracted {len(webcam_blocks)} WEBCAM visual blocks into neck_link_2.")
print(f"Added revolute joint 'neck_1_to_neck_2_joint' with Y axis from neck_link_1 to neck_link_2.")
