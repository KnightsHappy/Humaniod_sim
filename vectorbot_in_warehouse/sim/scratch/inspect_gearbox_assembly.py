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

gearbox_root_id = "MeS+fOPRnbEwZ2eaH"

print(f"Occurrences inside {inst_names[gearbox_root_id]}:")
for occ in occurrences:
    path = occ.get("path", [])
    if len(path) > 1 and path[0] == gearbox_root_id:
        path_names = [inst_names.get(node_id, node_id) for node_id in path]
        path_str = " -> ".join(path_names)
        transform = occ.get("transform")
        # Check if length of path is 2 or 3 and path has "gearbox" or "wheel" or "motor"
        if len(path) <= 3:
            if any("gearbox" in name.lower() or "motor" in name.lower() or "bottom" in name.lower() or "wheel" in name.lower() for name in path_names):
                print(f"\nPath: {path_str}")
                print(f"Transform (flat): {transform}")
                if transform:
                    mat = np.array(transform).reshape(4, 4)
                    print("Transform matrix:")
                    print(mat)
