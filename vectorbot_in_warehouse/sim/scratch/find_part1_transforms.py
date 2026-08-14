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

print(f"Part 1 occurrences under Gearbox+basebottom:")
for occ in occurrences:
    path = occ.get("path", [])
    if len(path) > 1 and path[0] == gearbox_root_id:
        path_names = [inst_names.get(node_id, node_id) for node_id in path]
        last_name = path_names[-1]
        if last_name.startswith("Part 1 ") or last_name == "Part 1":
            path_str = " -> ".join(path_names)
            transform = occ.get("transform")
            print(f"\nPath: {path_str}")
            print(f"Transform (flat): {transform}")
            if transform:
                mat = np.array(transform).reshape(4, 4)
                print("Transform matrix:")
                print(mat)
