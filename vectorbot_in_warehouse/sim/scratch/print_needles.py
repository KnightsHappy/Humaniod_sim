import re

def main():
    file_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro.bak2'
    with open(file_path, 'r') as f:
        content = f.read()
        
    visual_blocks = re.findall(r'(<visual>.*?</visual>)', content, re.DOTALL)
    for i, block in enumerate(visual_blocks):
        if 'ID_Needle_AXK_3047.stl' in block:
            origin = re.search(r'<origin xyz="([^"]+)" rpy="([^"]+)"', block)
            if origin:
                print(f"Visual {i}: xyz={origin.group(1)}, rpy={origin.group(2)}")

if __name__ == '__main__':
    main()
