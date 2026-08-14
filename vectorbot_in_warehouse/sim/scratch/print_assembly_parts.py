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
    print("Keys in response:", list(data.keys()))
    if 'parts' in data:
        print(f"Number of parts: {len(data['parts'])}")
        print("First part example:")
        print(json.dumps(data['parts'][0], indent=2))
    else:
        print("No 'parts' key found.")
else:
    print(f"Failed: {response.status_code}")
