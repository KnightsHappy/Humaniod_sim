import json
import numpy as np

json_path = "sim/scratch/assembly.json"
with open(json_path, "r") as f:
    data = json.load(f)

root = data.get("rootAssembly", {})
occurrences = root.get("occurrences", [])

print(f"Total occurrences: {len(occurrences)}")

for occ in occurrences:
    path = occ.get("path", [])
    transform = occ.get("transform")
    # Let's get the name or description of the instance in the path
    # The path elements refer to instance IDs. Let's find them in root['instances'] or sub-assemblies.
    # To make it simple, let's look at the occurrences of interest.
    # We can check if any instance in the path contains gearbox or wheel.
    # First, let's build a map from instance ID to name.
    # Instances can be in rootAssembly or in subassemblies.
    # Let's collect all instances.
    inst_names = {}
    
    # 1. Root assembly instances
    for inst in root.get("instances", []):
        inst_names[inst.get("id")] = inst.get("name")
        
    # 2. Sub-assemblies instances
    for sa in data.get("subAssemblies", []):
        for inst in sa.get("instances", []):
            inst_names[inst.get("id")] = inst.get("name")
            
    # 3. Parts
    for part in data.get("parts", []):
        # Parts don't have instances themselves, but instances can be parts.
        pass

    path_names = [inst_names.get(node_id, node_id) for node_id in path]
    path_str = " -> ".join(path_names)
    
    if any("gearbox" in name.lower() or "wheel" in name.lower() for name in path_names):
        print(f"\nPath: {path_str}")
        print(f"Transform (flat): {transform}")
        if transform:
            mat = np.array(transform).reshape(4, 4)
            print("Transform matrix:")
            print(mat)
