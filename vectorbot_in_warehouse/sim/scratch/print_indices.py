import re

def main():
    file_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro'
    
    with open(file_path, 'r') as f:
        content = f.read()
        
    torso_match = re.search(r'<link name="torso_link">(.*?)</link>', content, re.DOTALL)
    if not torso_match:
        print("torso_link not found!")
        return
        
    torso_content = torso_match.group(1)
    visual_blocks = re.findall(r'(<visual>.*?</visual>)', torso_content, re.DOTALL)
    
    for i in range(110, 170):
        if i < len(visual_blocks):
            block = visual_blocks[i]
            mesh_match = re.search(r'mesh filename="([^"]+)"', block)
            mesh = mesh_match.group(1).split('/')[-1] if mesh_match else "None"
            origin = re.search(r'origin xyz="([^"]+)"', block)
            origin_str = origin.group(1) if origin else "None"
            print(f"Index {i}: {mesh:<40} | Origin: {origin_str}")

if __name__ == '__main__':
    main()
