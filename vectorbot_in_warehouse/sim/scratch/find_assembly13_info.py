import json
import numpy as np

json_path = "sim/scratch/assembly.json"
with open(json_path, "r") as f:
    data = json.load(f)

root = data.get("rootAssembly", {})
occurrences = root.get("occurrences", [])

# Build maps from elementId to subassembly
sub_assemblies = {}
for sa in data.get("subAssemblies", []):
    eid = sa.get("elementId")
    sub_assemblies[eid] = sa

path_to_names = {}

def traverse(curr_sa, parent_path_ids, parent_path_names):
    instances = curr_sa.get("instances", [])
    for inst in instances:
        inst_id = inst.get("id")
        inst_name = inst.get("name")
        inst_type = inst.get("type")
        
        path_ids = parent_path_ids + [inst_id]
        path_names = parent_path_names + [inst_name]
        
        path_to_names[tuple(path_ids)] = path_names
        
        if inst_type == "Assembly":
            eid = inst.get("elementId")
            if eid in sub_assemblies:
                traverse(sub_assemblies[eid], path_ids, path_names)
            else:
                for sa in data.get("subAssemblies", []):
                    if sa.get("elementId") == eid:
                        traverse(sa, path_ids, path_names)
                        break

traverse(root, [], [])

print("Scanning all occurrences for Assembly 1 elements:")
for occ in occurrences:
    path = tuple(occ.get("path", []))
    path_names = path_to_names.get(path)
    if path_names:
        path_str = " -> ".join(path_names)
        if "Assembly 1 <1>" in path_str:
            last_name = path_names[-1]
            if "Part 1 " in last_name or "Part 13" in last_name or last_name == "Part 1" or last_name == "Part 13":
                transform = occ.get("transform")
                if transform:
                    mat = np.array(transform).reshape(4, 4)
                    print(f"\nPath: {path_str}")
                    print(f"Translation: x={mat[0,3]:.6f}, y={mat[1,3]:.6f}, z={mat[2,3]:.6f}")
