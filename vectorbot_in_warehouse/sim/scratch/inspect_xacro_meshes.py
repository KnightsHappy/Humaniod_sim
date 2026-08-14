import re

xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"

with open(xacro_path, "r") as f:
    content = f.read()

# Let's find all '<link' definitions in vector.xacro
link_pattern = re.compile(r'<link\s+name="([^"]+)">.*?</link>', re.DOTALL)
links = link_pattern.findall(content)

print("=== XACRO LINK MESHES ===")
for name in links:
    link_content_match = re.search(r'<link\s+name="' + re.escape(name) + r'">.*?</link>', content, re.DOTALL)
    if link_content_match:
        link_content = link_content_match.group(0)
        meshes = re.findall(r'<mesh\s+filename="package://[^/]+/meshes/([^"]+)"', link_content)
        print(f"Link: {name}")
        print(f"  Meshes: {meshes}")
