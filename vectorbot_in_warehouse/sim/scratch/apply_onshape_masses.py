import json
import re
import numpy as np

# Paths
xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"
json_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/onshape_mass_data.json"

# Load Onshape raw mass data
with open(json_path, "r") as f:
    data = json.load(f)

# Global frame origins of each link (accumulated translations from base_link)
frames = {
    "base_link": np.array([0.0, 0.0, 0.0]),
    "torso_link": np.array([0.150000, 0.000000, 0.991427]),
    "shoulder_link_1_link": np.array([-0.122176, 0.052366, 1.022100]),
    "shoulder_link_2": np.array([-0.145326, 0.113366, 1.022100]),
    "elbow_link_1": np.array([-0.211941, 0.048354, 0.969100]),
    "elbow_link_2": np.array([-0.225819, 0.072677, 0.740400]),
    "right_shoulder_link_1": np.array([0.191824, 0.052366, 1.022101]),
    "right_shoulder_link_2": np.array([0.214974, 0.113366, 1.022100]),
    "right_elbow_link_1": np.array([0.281589, 0.048354, 0.969100]),
    "right_elbow_link_2": np.array([0.295467, 0.072677, 0.740400]),
    "wrist_link_1": np.array([0.332657, 0.189256, 1.363048]),
    "ee_link": np.array([0.330968, 0.167681, 1.448750])
}

# ee_link occurrence transform R & t from Onshape
R_ee = np.array([
    [0.999254075443207, 0.03515289107545025, -0.0159864617466982],
    [0.034614845998456004, -0.998863263775754, -0.032771828080710004],
    [-0.017120313859397798, 0.032194013857951446, -0.999334999049403]
])
t_ee = np.array([0.332188867727933, 0.16662731260674798, 1.48780217571856])

with open(xacro_path, "r") as f:
    content = f.read()

for link_name, link_data in data.items():
    mass = link_data["mass"]
    centroid_global = np.array(link_data["centroid"])
    inertia_raw = link_data["inertia"]
    
    if link_name == "ee_link":
        # ee_link is a Part: transform centroid to global first, then to local link frame
        centroid_global = R_ee @ centroid_global + t_ee
        
        # Build local 3x3 inertia matrix
        I_local = np.array([
            [inertia_raw[0], inertia_raw[1], inertia_raw[2]],
            [inertia_raw[3], inertia_raw[4], inertia_raw[5]],
            [inertia_raw[6], inertia_raw[7], inertia_raw[8]]
        ])
        # Rotate inertia tensor to global/link frame: R @ I @ R.T
        I_rotated = R_ee @ I_local @ R_ee.T
        
        ixx, ixy, ixz = I_rotated[0, 0], I_rotated[0, 1], I_rotated[0, 2]
        iyy, iyz = I_rotated[1, 1], I_rotated[1, 2]
        izz = I_rotated[2, 2]
    else:
        # Assembly link: centroid is global, inertia is already about COM & global-aligned
        ixx, ixy, ixz = inertia_raw[0], inertia_raw[1], inertia_raw[2]
        iyy, iyz = inertia_raw[4], inertia_raw[5]
        izz = inertia_raw[8]
        
    # Calculate local centroid: global_centroid - frame_origin
    centroid_local = centroid_global - frames[link_name]
    
    # Generate new XML block
    # Determine the link indentation
    # Let's inspect the original match to see its indentation style, or use standard double space / 4 spaces
    # Let's check how the original block looked. We'll use 8 spaces indentation inside <inertial>
    new_inertial = (
        f"\n        <inertial>\n"
        f"            <mass value=\"{mass:.6f}\" />\n"
        f"            <origin xyz=\"{centroid_local[0]:.6f} {centroid_local[1]:.6f} {centroid_local[2]:.6f}\" rpy=\"0 0 0\" />\n"
        f"            <inertia ixx=\"{ixx:.9e}\" ixy=\"{ixy:.9e}\" ixz=\"{ixz:.9e}\" iyy=\"{iyy:.9e}\" iyz=\"{iyz:.9e}\" izz=\"{izz:.9e}\" />\n"
        f"        </inertial>"
    )
    
    # Regex search and replace
    pattern = rf'(<link\s+name="{link_name}">\s*<inertial>)(.*?)(</inertial>)'
    
    # Replaces the whole matched block with the link tag + new inertial block
    # We want to replace the match of <link name="...">\s*<inertial>...</inertial>
    # Group 1: <link name="...">\s*<inertial>
    # Group 2: ... (the old block to replace)
    # Group 3: </inertial>
    
    # Let's do search and replace
    def repl(match):
        # Determine prefix and spacing
        prefix = match.group(1)
        # We replace the internal content (group 2) and </inertial> (group 3) with our new block
        # Wait, since group 1 ends with <inertial>, we can just replace everything from <inertial> to </inertial>
        # To make it very clean:
        # Let's just find the start of '<inertial>' and end of '</inertial>' inside the match
        m_text = match.group(0)
        # Replace from <inertial> to </inertial>
        # We want to replace <inertial>...</inertial> with new_inertial
        # But wait! If we do that, we should keep the `<link name="...">` part intact.
        # Let's write the substitution explicitly:
        link_tag = match.group(1).split("<inertial>")[0]
        return f"{link_tag}{new_inertial}"

    content, count = re.subn(pattern, repl, content, flags=re.DOTALL)
    print(f"Updated {link_name} ({count} matches replaced):")
    print(f"  Mass: {mass:.6f}")
    print(f"  COM:  {centroid_local[0]:.6f} {centroid_local[1]:.6f} {centroid_local[2]:.6f}")

# Write the modified content back
with open(xacro_path, "w") as f:
    f.write(content)
print("Finished updating vector.xacro successfully!")
