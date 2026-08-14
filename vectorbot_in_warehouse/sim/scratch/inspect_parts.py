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
    parts = data.get('parts', [])
    print(f"Total parts in list: {len(parts)}")
    
    # Print parts that have different keys or interesting properties
    non_empty_part_ids = [p for p in parts if p.get('partId')]
    print(f"Parts with non-empty partId: {len(non_empty_part_ids)}")
    
    for i, p in enumerate(parts[:10]):
        print(f"Part {i}: keys={list(p.keys())}")
        print(f"  elementId: {p.get('elementId')}")
        print(f"  partId: {p.get('partId')}")
        print(f"  documentId: {p.get('documentId')}")
else:
    print("Failed to fetch")
