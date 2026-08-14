import requests
from requests.auth import HTTPBasicAuth
import numpy as np
import json

ACCESS_KEY = "on_ZBYH1toFedwHtBWhgI1wX"
SECRET_KEY = "v8l3gYHedapodnDXImXq9NpztNIWOQ9lD8AWpIHryHeZu95S"
DID = "c6f6216d8062a2927a42dbbe"
WID = "d0059b9eedacc9158e955397"

eids = {
    "Assembly 1": "19eee708f712621e03bd563c",
    "Assembly 12": "898e666595c388cd2612aac2",
    "Gearbox+basebottom": "7caab4dd055bcbef1fa65efe"
}

headers = {
    "Accept": "application/json; charset=UTF-8",
    "Content-Type": "application/json"
}

sub_masses = []
sub_centroids = []
sub_inertias = [] # inertia tensors about COM

for name, eid in eids.items():
    url = f"https://cad.onshape.com/api/v1/assemblies/d/{DID}/w/{WID}/e/{eid}/massproperties"
    response = requests.get(url, auth=HTTPBasicAuth(ACCESS_KEY, SECRET_KEY), headers=headers)
    if response.status_code == 200:
        data = response.json()
        mass = data.get("mass", [0])[0]
        centroid = np.array(data.get("centroid", [0, 0, 0])[:3])
        if name == "Gearbox+basebottom":
            t_gearbox = np.array([0.008511724783650573, -0.0034115864586085065, 0.009621370568228177])
            centroid += t_gearbox

        
        # Onshape returns inertia as 9 values
        # representing the 3x3 symmetric inertia matrix about COM
        inertia_val = data.get("inertia", [0]*9)[:9]
        I_com = np.array([
            [inertia_val[0], inertia_val[1], inertia_val[2]],
            [inertia_val[3], inertia_val[4], inertia_val[5]],
            [inertia_val[6], inertia_val[7], inertia_val[8]]
        ])
        
        sub_masses.append(mass)
        sub_centroids.append(centroid)
        sub_inertias.append(I_com)
        print(f"Fetched {name}: mass={mass:.4f} kg")
    else:
        print(f"Failed to fetch {name}: {response.status_code}")
        exit(1)

# 1. Compute combined mass
total_mass = sum(sub_masses)

# 2. Compute combined centroid
combined_centroid = np.zeros(3)
for m, c in zip(sub_masses, sub_centroids):
    combined_centroid += m * c
combined_centroid /= total_mass

# 3. Compute combined inertia tensor about the combined centroid (Parallel Axis Theorem)
# For each subassembly: I_combined_com = I_sub_com + m * ( (d.d) * E - d * d^T )
# where d = sub_centroid - combined_centroid
I_combined = np.zeros((3, 3))
for m, c, I_com in zip(sub_masses, sub_centroids, sub_inertias):
    d = c - combined_centroid
    d_sq = np.dot(d, d)
    # m * ( d_sq * identity - outer(d, d) )
    I_parallel = m * (d_sq * np.eye(3) - np.outer(d, d))
    I_combined += I_com + I_parallel

print("\n--- COMBINED PROPERTIES FOR base_link ---")
print(f"Total Mass: {total_mass:.6f} kg")
print(f"Combined Centroid (xyz): {combined_centroid.tolist()}")
print("Combined Inertia Tensor about COM (3x3):")
print(I_combined)

ixx = I_combined[0, 0]
ixy = I_combined[0, 1]
ixz = I_combined[0, 2]
iyy = I_combined[1, 1]
iyz = I_combined[1, 2]
izz = I_combined[2, 2]

print(f"\nixx=\"{ixx:.9e}\" ixy=\"{ixy:.9e}\" ixz=\"{ixz:.9e}\" iyy=\"{iyy:.9e}\" iyz=\"{iyz:.9e}\" izz=\"{izz:.9e}\"")
