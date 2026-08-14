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

# Find occurrences containing Assembly 13
for occ in occurrences:
    path = occ.get("path", [])
    path_names = [inst_names.get(node_id, node_id) for node_id in path]
    path_str = " -> ".join(path_names)
    
    if "Assembly 13" in path_str:
        print(f"\nPath: {path_str}")
        transform = occ.get("transform")
        if transform:
            mat = np.array(transform).reshape(4, 4)
            print(f"Translation: x={mat[0,3]:.6f}, y={mat[1,3]:.6f}, z={mat[2,3]:.6f}")
