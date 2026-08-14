import requests
from requests.auth import HTTPBasicAuth
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

for name, eid in eids.items():
    url = f"https://cad.onshape.com/api/v1/assemblies/d/{DID}/w/{WID}/e/{eid}/massproperties"
    response = requests.get(url, auth=HTTPBasicAuth(ACCESS_KEY, SECRET_KEY), headers=headers)
    if response.status_code == 200:
        data = response.json()
        mass = data.get("mass", [0])[0]
        centroid = data.get("centroid", [0, 0, 0])[:3]
        print(f"{name}: mass={mass:.4f} kg | centroid={centroid}")
    else:
        print(f"Failed for {name}: {response.status_code}")
