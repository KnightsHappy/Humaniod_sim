import requests
from requests.auth import HTTPBasicAuth
import json

ACCESS_KEY = "on_ZBYH1toFedwHtBWhgI1wX"
SECRET_KEY = "v8l3gYHedapodnDXImXq9NpztNIWOQ9lD8AWpIHryHeZu95S"
DID = "c6f6216d8062a2927a42dbbe"
WID = "d0059b9eedacc9158e955397"

targets = {
    "base_link": {"type": "assembly", "eid": "7caab4dd055bcbef1fa65efe"},
    "torso_link": {"type": "assembly", "eid": "6984f365c016400ea360c564"},
    "shoulder_link_1_link": {"type": "assembly", "eid": "254460139c26bd110213f74b"},
    "shoulder_link_2": {"type": "assembly", "eid": "397182d1d6810b9ba3d33bc3"},
    "elbow_link_1": {"type": "assembly", "eid": "b04a533832bcebff7493599e"},
    "elbow_link_2": {"type": "assembly", "eid": "b2a8fca4c2aa407bb2c06531"},
    "right_shoulder_link_1": {"type": "assembly", "eid": "419ddccbc787ed8fbf56a882"},
    "right_shoulder_link_2": {"type": "assembly", "eid": "eab7c3e09af32a2b757345b0"},
    "right_elbow_link_1": {"type": "assembly", "eid": "24c262bd80e8674189485253"},
    "right_elbow_link_2": {"type": "assembly", "eid": "31b8b3cd5c40b5dc7c2e9f5a"},
    "wrist_link_1": {"type": "assembly", "eid": "1f797ef8f58aeddbe01e5728"},
    "ee_link": {"type": "part", "eid": "6b4f2a922b8ffcac531e6916", "partid": "KFLt"}
}

headers = {
    "Accept": "application/json; charset=UTF-8",
    "Content-Type": "application/json"
}

results = {}

for name, info in targets.items():
    if info["type"] == "assembly":
        url = f"https://cad.onshape.com/api/v1/assemblies/d/{DID}/w/{WID}/e/{info['eid']}/massproperties"
    else:
        url = f"https://cad.onshape.com/api/v1/parts/d/{DID}/w/{WID}/e/{info['eid']}/partid/{info['partid']}/massproperties"
        
    response = requests.get(url, auth=HTTPBasicAuth(ACCESS_KEY, SECRET_KEY), headers=headers)
    if response.status_code == 200:
        data = response.json()
        # Parse based on structure
        if info["type"] == "part":
            body_data = data.get("bodies", {}).get(info["partid"], {})
        else:
            body_data = data
            
        results[name] = {
            "mass": body_data.get("mass", [0])[0],
            "centroid": body_data.get("centroid", [0, 0, 0])[:3],
            "inertia": body_data.get("inertia", [0]*9)[:9]
        }
        print(f"Fetched {name}: mass={results[name]['mass']:.5f}")
    else:
        print(f"Failed to fetch {name}: {response.status_code}")

# Write to file
with open("/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/onshape_mass_data.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved all mass properties to scratch/onshape_mass_data.json")
