import json
import numpy as np

json_path = "sim/scratch/assembly.json"
with open(json_path, "r") as f:
    data = json.load(f)

# Let's find the subassembly named Base-motor+gearbox-subassembly
subassemblies = data.get("subAssemblies", [])
target_sa = None
for sa in subassemblies:
    if "Base-motor" in sa.get("name", ""):
        target_sa = sa
        print(f"Found subassembly: {sa.get('name')} (ID: {sa.get('elementId')})")
        break

if target_sa:
    instances = target_sa.get("instances", [])
    print("Instances inside it:")
    for inst in instances:
        print(f"  ID: {inst.get('id'):30} | Name: {inst.get('name'):40} | Type: {inst.get('type')}")
