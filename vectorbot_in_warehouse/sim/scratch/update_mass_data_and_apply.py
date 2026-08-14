import json
import subprocess

json_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/onshape_mass_data.json"

# Load current data
with open(json_path, "r") as f:
    data = json.load(f)

# Update base_link
data["base_link"] = {
    "mass": 66.476139,
    "centroid": [0.049547, -0.005405, 0.025724],
    "inertia": [
        5.079439634, -0.02193859608, -0.1312023858,
        -0.02193859608, 4.725292650, 0.5987075030,
        -0.1312023858, 0.5987075030, 2.926682437
    ]
}

# Save back to JSON
with open(json_path, "w") as f:
    json.dump(data, f, indent=2)

print("Updated base_link in onshape_mass_data.json")

# Run apply_onshape_masses.py
res = subprocess.run(["python3", "/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/apply_onshape_masses.py"], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print("Errors:")
    print(res.stderr)
