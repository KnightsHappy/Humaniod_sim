import re

def main():
    file_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro'
    with open(file_path, 'r') as f:
        content = f.read()

    torso_match = re.search(r'<link name="torso_link">(.*?)</link>', content, re.DOTALL)
    torso_content = torso_match.group(1)
    visual_blocks = re.findall(r'(<visual>.*?</visual>)', torso_content, re.DOTALL)

    print("Printing all visual blocks from index 50 to 115:")
    for i in range(50, min(116, len(visual_blocks))):
        block = visual_blocks[i]
        mesh_match = re.search(r'mesh filename="file://\$\(find vector_description\)/meshes/([^"]+)"', block)
        mesh_name = mesh_match.group(1) if mesh_match else "No mesh"
        origin = re.search(r'origin xyz="([^"]+)"', block)
        origin_xyz = origin.group(1) if origin else "No origin"
        print(f"Index {i:3d}: {mesh_name:<50} | XYZ: {origin_xyz}")

if __name__ == '__main__':
    main()
