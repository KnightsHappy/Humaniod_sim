import re

xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"

with open(xacro_path, 'r') as f:
    content = f.read()

links = [
    "base_link",
    "torso_link",
    "shoulder_link_1_link",
    "shoulder_link_2",
    "elbow_link_1",
    "elbow_link_2",
    "right_shoulder_link_1",
    "right_shoulder_link_2",
    "right_elbow_link_1",
    "right_elbow_link_2",
    "wrist_link_1",
    "ee_link"
]

print("Regex matching test:")
for link in links:
    pattern = rf'(<link\s+name="{link}">\s*<inertial>)(.*?)(</inertial>)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        print(f"  Matched {link}!")
    else:
        print(f"  FAILED to match {link}")
