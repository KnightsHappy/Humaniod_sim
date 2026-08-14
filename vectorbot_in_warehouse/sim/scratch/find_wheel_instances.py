import json
import numpy as np

json_path = "sim/scratch/assembly.json"
with open(json_path, "r") as f:
    data = json.load(f)

root = data.get("rootAssembly", {})
occurrences = root.get("occurrences", [])

# Map from instance ID to name
inst_names = {}
for inst in root.get("instances", []):
    inst_names[inst.get("id")] = inst.get("name")
for sa in data.get("subAssemblies", []):
    for inst in sa.get("instances", []):
        inst_names[inst.get("id")] = inst.get("name")

# Also let's find the instances matching partId 'JFv' (which is Part_1.stl)
wheel_part_instances = set()
for inst in root.get("instances", []):
    if inst.get("partId") == "JFv":
        wheel_part_instances.add(inst.get("id"))
for sa in data.get("subAssemblies", []):
    for inst in sa.get("instances", []):
        if inst.get("partId") == "JFv":
            wheel_part_instances.add(inst.get("id"))

print(f"Wheel Part Instances: {wheel_part_instances}")

print("\nOccurrences of wheels:")
for occ in occurrences:
    path = occ.get("path", [])
    if any(node_id in wheel_part_instances for node_id in path):
        path_names = [inst_names.get(node_id, node_id) for node_id in path]
        path_str = " -> ".join(path_names)
        transform = occ.get("transform")
        print(f"\nPath: {path_str}")
        print(f"Transform (flat): {transform}")
        if transform:
            mat = np.array(transform).reshape(4, 4)
            print("Transform matrix:")
            print(mat)
