import re

def extract_block(content, tag_name, name_attribute):
    if tag_name == 'joint':
        # Match only revolute joints, not other tags/nodes with similar name
        pattern = rf'(<joint\s+[^>]*name="{name_attribute}"[^>]*type="revolute"[^>]*>.*?</joint>)'
    else:
        pattern = rf'(<link\s+name="{name_attribute}">.*?</link>)'
    
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1) if match else None

def main():
    urdf_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/vector.urdf'
    xacro_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro'

    with open(urdf_path, 'r') as f:
        urdf_content = f.read()

    with open(xacro_path, 'r') as f:
        xacro_content = f.read()

    blocks = [
        ('link', 'shoulder_link_2'),
        ('joint', 'left_shoulder'),
        ('link', 'elbow_link_1'),
        ('joint', 'left_bicep'),
        ('link', 'elbow_link_2'),
        ('joint', 'left_forearm')
    ]

    updated_xacro = xacro_content

    for tag, name in blocks:
        urdf_block = extract_block(urdf_content, tag, name)
        if not urdf_block:
            print(f"Error: Could not extract {tag} '{name}' from URDF!")
            return

        # Adapt file paths in the URDF block
        adapted_block = urdf_block.replace(
            'file:///home/nihit/bots/vectorbot_in_warehouse/sim/install/vector_description/share/vector_description/meshes/',
            'file://$(find vector_description)/meshes/'
        )

        # Extract corresponding block from xacro to replace it
        xacro_block = extract_block(updated_xacro, tag, name)
        if not xacro_block:
            print(f"Error: Could not find {tag} '{name}' in xacro!")
            return

        print(f"Replacing {tag} '{name}'...")
        updated_xacro = updated_xacro.replace(xacro_block, adapted_block)

    with open(xacro_path, 'w') as f:
        f.write(updated_xacro)

    print("Success: vector.xacro updated successfully!")

if __name__ == '__main__':
    main()
