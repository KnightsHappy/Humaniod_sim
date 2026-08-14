with open("/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro", "r") as f:
    content = f.read()

# Let's find all '<link' definitions in vector.xacro
import re

link_pattern = re.compile(r'<link\s+name="([^"]+)">.*?</link>', re.DOTALL)
links = link_pattern.findall(content)

print(f"Found {len(links)} links in vector.xacro:")
for name in links:
    # Extract name and inertial
    link_content_match = re.search(r'<link\s+name="' + re.escape(name) + r'">.*?</link>', content, re.DOTALL)
    if link_content_match:
        link_content = link_content_match.group(0)
        inertial_match = re.search(r'<inertial>.*?</inertial>', link_content, re.DOTALL)
        if inertial_match:
            print(f"Link name: {name}")
            print(inertial_match.group(0))
            print("-" * 50)
        else:
            print(f"Link name: {name} (No inertial)")
