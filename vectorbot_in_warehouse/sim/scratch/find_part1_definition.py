import json

json_path = "sim/scratch/assembly.json"
with open(json_path, "r") as f:
    data = json.load(f)

# Find definition of Part 1 in data['parts']
parts = data.get("parts", [])
print(f"Total parts: {len(parts)}")
for part in parts:
    name = part.get("name", "")
    if "part 1" in name.lower() or name == "Part 1":
        print(f"Part Name: {name}")
        print(f"Part ID: {part.get('partId')}")
        print(f"Element ID: {part.get('elementId')}")
        print(f"Keys: {part.keys()}")
