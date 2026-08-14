import json

json_path = "sim/scratch/assembly.json"
with open(json_path, "r") as f:
    data = json.load(f)

# Collect all instance names across rootAssembly and all subAssemblies
names = set()
for inst in data.get("rootAssembly", {}).get("instances", []):
    names.add(inst.get("name"))
for sa in data.get("subAssemblies", []):
    for inst in sa.get("instances", []):
        names.add(inst.get("name"))

for name in sorted(list(names)):
    if "Assembly" in name or "assembly" in name.lower() or "lidar" in name.lower():
        print(name)
