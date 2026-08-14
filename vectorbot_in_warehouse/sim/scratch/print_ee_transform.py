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
    
    # Let's map instance names to make path lookup human-readable
    instance_names = {}
    
    def gather_instances(sa):
        for inst in sa.get('instances', []):
            instance_names[inst['id']] = inst.get('name')
            
    gather_instances(root)
    for sa in data.get('subAssemblies', []):
        gather_instances(sa)
        
    print("Occurrences matching Hand-EE:")
    for occ in root.get('occurrences', []):
        path = occ.get('path', [])
        path_names = [instance_names.get(pid, pid) for pid in path]
        if any('Hand-EE' in name for name in path_names if name):
            print(f"Path: {' -> '.join(path_names)}")
            print(f"Transform: {occ.get('transform')}")
else:
    print("Failed")
