import json

json_path = "sim/scratch/assembly.json"
with open(json_path, "r") as f:
    data = json.load(f)

# The parts list might not contain masses directly, but let's check
# Or let's check the instances whose mass is around 0.795 kg in the parts properties or metadata.
# Let's search data['parts'] first
parts = data.get("parts", [])
print(f"Total parts in JSON: {len(parts)}")
for part in parts:
    # Let's print keys of a part first to see what properties are available
    # print(part.keys())
    # break
    pass

# Let's look at the subassemblies and instances
# Let's search for instances with mass in their names or let's write a script to search for the word 'wheel' or check all Part 1 instances.
# Wait, let's look at the partIds of all instances in sa.get('instances', []) and root.get('instances', [])
# and see which ones are from elementId '6b4f2a922b8ffcac531e6916' (since that's the wheel studio).
wheel_studio_id = "6b4f2a922b8ffcac531e6916"
matching_insts = []
for inst in root.get("instances", []):
    if inst.get("elementId") == wheel_studio_id:
        matching_insts.append(("root", inst))
for sa in data.get("subAssemblies", []):
    for inst in sa.get("instances", []):
        if inst.get("elementId") == wheel_studio_id:
            matching_insts.append((sa.get("elementId"), inst))

print(f"\nInstances from wheel studio (elementId: {wheel_studio_id}):")
for origin, inst in matching_insts:
    print(f"Origin: {origin} | Name: {inst.get('name'):30} | partId: {inst.get('partId')}")
