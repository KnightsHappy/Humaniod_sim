import re

def main():
    file_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro'
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    in_torso_link = False
    new_lines = []
    
    # We will shift torso_link meshes by:
    dx, dy, dz = 0.15, 0.0, 0.991427
    
    # Track link scope
    for i, line in enumerate(lines):
        # Detect torso_link start and end
        if '<link name="torso_link">' in line:
            in_torso_link = True
            print(f"Entering torso_link at line {i+1}")
        elif in_torso_link and '</link>' in line:
            in_torso_link = False
            print(f"Exiting torso_link at line {i+1}")
            
        # Parse and shift origin inside torso_link
        if in_torso_link and 'origin xyz=' in line:
            match = re.search(r'origin xyz="([^"]+)"', line)
            if match:
                xyz_str = match.group(1)
                xyz = [float(val) for val in xyz_str.split()]
                new_xyz = [xyz[0] - dx, xyz[1] - dy, xyz[2] - dz]
                new_xyz_str = f"{new_xyz[0]:.6f} {new_xyz[1]:.6f} {new_xyz[2]:.6f}"
                line = line.replace(f'xyz="{xyz_str}"', f'xyz="{new_xyz_str}"')
                
        # Parse and update torso_joint origin
        if '<joint name="torso_joint"' in line:
            # Look ahead to find its origin and update it
            print(f"Found torso_joint at line {i+1}")
        
        # We can do a second pass or simple state-machine for joints
        new_lines.append(line)
        
    # Joint modifications using regex / direct replacement
    content = "".join(new_lines)
    
    # Update torso_joint origin
    torso_joint_pattern = r'(<joint name="torso_joint" type="prismatic">.*?<origin xyz=")[^"]+(" rpy="0 0 0" />)'
    content, count1 = re.subn(torso_joint_pattern, r'\g<1>0.150000 0.000000 0.991427\g<2>', content, flags=re.DOTALL)
    print(f"Updated torso_joint origin: {count1} occurrence(s)")
    
    # Update shoulder_link_1 origin
    shoulder_joint_pattern = r'(<joint name="shoulder_link_1" type="revolute">.*?<origin xyz=")[^"]+(" rpy="0 0 0" />)'
    content, count2 = re.subn(shoulder_joint_pattern, r'\g<1>-0.272176 0.052366 0.030673\g<2>', content, flags=re.DOTALL)
    print(f"Updated shoulder_link_1 origin: {count2} occurrence(s)")
    
    # Save the file
    with open(file_path, 'w') as f:
        f.write(content)
    print("Refactoring complete.")

if __name__ == '__main__':
    main()
