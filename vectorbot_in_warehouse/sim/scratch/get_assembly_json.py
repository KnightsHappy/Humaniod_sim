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
    with open('/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/assembly.json', 'w') as f:
        json.dump(response.json(), f, indent=2)
    print("Successfully saved assembly JSON!")
else:
    print(f"Failed: {response.status_code} - {response.text}")
