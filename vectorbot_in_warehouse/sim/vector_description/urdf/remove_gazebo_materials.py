import re

file_path = '/home/karan/vectorbots/sim/vector_description/urdf/vector.gazebo'

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if '<material>Gazebo/' in line:
        continue
    new_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print("Removed all Gazebo material scripts.")
