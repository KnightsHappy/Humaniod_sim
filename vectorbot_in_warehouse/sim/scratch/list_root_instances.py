import json

json_path = "sim/scratch/assembly.json"
with open(json_path, "r") as f:
    data = json.load(f)

root = data.get("rootAssembly", {})
instances = root.get("instances", [])
occurrences = root.get("occurrences", [])

# Map from instance ID to name
inst_name = {inst.get("id"): inst.get("name") for inst in instances}

print("Root Assembly Instances:")
for inst in instances:
    print(f"ID: {inst.get('id'):30} | Name: {inst.get('name'):40} | Type: {inst.get('type')}")

print("\nRoot Occurrences (transform of instances directly under root):")
for occ in occurrences:
    path = occ.get("path", [])
    if len(path) == 1:
        # Direct child of root
        inst_id = path[0]
        name = inst_name.get(inst_id, inst_id)
        transform = occ.get("transform")
        print(f"Name: {name:40} | Transform: {transform}")
