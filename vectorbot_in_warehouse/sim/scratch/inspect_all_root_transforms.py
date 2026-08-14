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

eids = {
    "Assembly 1": "19eee708f712621e03bd563c",
    "Assembly 12": "898e666595c388cd2612aac2",
    "Gearbox+basebottom": "7caab4dd055bcbef1fa65efe"
}

response = requests.get(url, auth=HTTPBasicAuth(ACCESS_KEY, SECRET_KEY), headers=headers)
if response.status_code == 200:
    data = response.json()
    root = data.get('rootAssembly', {})
    print("Root occurrences:")
    for inst in root.get('instances', []):
        name = inst.get('name')
        for occ in root.get('occurrences', []):
            if occ.get('path') == [inst['id']]:
                print(f"Name: {name:45} | Transform: {occ.get('transform')}")
else:
    print("Failed")
