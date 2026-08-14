import json
import numpy as np

with open('/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/assembly.json') as f:
    data = json.load(f)

# Build quick lookup maps
instances = {}
for sa in data.get('subAssemblies', []) + [data.get('rootAssembly', {})]:
    for inst in sa.get('instances', []):
        instances[inst['id']] = inst

# Helper to get full path name
def get_path_name(path):
    names = []
    for inst_id in path:
        inst = instances.get(inst_id)
        if inst:
            names.append(inst['name'])
        else:
            names.append(inst_id)
    return " -> ".join(names)

print("Mates in Assembly:")
mate_features = data.get('rootAssembly', {}).get('mateFeatures', [])
for mate in mate_features:
    print(f"Mate: {mate.get('name')}, Type: {mate.get('mateType')}")

# Print occurrences for left arm
print("\nLeft Arm Part Occurrences and Transforms:")
for occ in data.get('rootAssembly', {}).get('occurrences', []):
    path = occ.get('path', [])
    path_name = get_path_name(path)
    if 'leftarm' in path_name.lower() or 'e1' in path_name.lower() or 'e2' in path_name.lower():
        transform = occ.get('transform')
        if transform:
            # transform is a 16-element array (4x4 matrix, row-major or column-major?)
            # Onshape returns column-major 4x4 matrix, so transform[12:15] is the translation vector.
            # Let's check or print it as a matrix.
            mat = np.array(transform).reshape(4, 4)
            translation = mat[3, 0:3] if mat[0, 3] == 0 else mat[0:3, 3] # typically column major or row major, let's look at the last column/row
            # Let's print the translation part
            print(f"{path_name}:")
            print(f"  Translation: {transform[12:15]} (last row/column: {transform[3]}, {transform[7]}, {transform[11]}, {transform[15]})")
            print(f"  Matrix: {transform}")
