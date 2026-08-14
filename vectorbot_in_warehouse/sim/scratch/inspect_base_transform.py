import requests
from requests.auth import HTTPBasicAuth
import json

ACCESS_KEY = "on_ZBYH1toFedwHtBWhgI1wX"
SECRET_KEY = "v8l3gYHedapodnDXImXq9NpztNIWOQ9lD8AWpIHryHeZu95S"
DID = "c6f6216d8062a2927a42dbbe"
WID = "d0059b9eedacc9158e955397"
EID = "90e7b5777f61e72dfddbc835"

url = f"https://cad.onshape.com/api/v1/assemblies/d/{DID}/w/{WID}/e/{EID}"

headers = {
    "Accept": "application/json; charset=UTF-8",
    "Content-Type": "application/json"
}

response = requests.get(url, auth=HTTPBasicAuth(ACCESS_KEY, SECRET_KEY), headers=headers)
if response.status_code == 200:
    data = response.json()
    root = data.get('rootAssembly', {})
    print("Instance transforms matching basebottom/torso:")
    for inst in root.get('instances', []):
        if 'Gearbox' in inst.get('name') or 'Torso' in inst.get('name'):
            # Find the transform for this instance in occurrences
            for occ in root.get('occurrences', []):
                if occ.get('path') == [inst['id']]:
                    print(f"Name: {inst['name']:40} | Transform: {occ.get('transform')}")
else:
    print("Failed")
