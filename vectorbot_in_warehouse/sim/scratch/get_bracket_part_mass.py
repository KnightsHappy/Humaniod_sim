import requests
from requests.auth import HTTPBasicAuth
import json

ACCESS_KEY = "on_ZBYH1toFedwHtBWhgI1wX"
SECRET_KEY = "v8l3gYHedapodnDXImXq9NpztNIWOQ9lD8AWpIHryHeZu95S"
DID = "c6f6216d8062a2927a42dbbe"
WID = "d0059b9eedacc9158e955397"
EID = "6b4f2a922b8ffcac531e6916"
PARTID = "KF/s" # L-S2-bracket

url = f"https://cad.onshape.com/api/v1/parts/d/{DID}/w/{WID}/e/{EID}/partid/{PARTID}/massproperties"

headers = {
    "Accept": "application/json; charset=UTF-8",
    "Content-Type": "application/json"
}

response = requests.get(url, auth=HTTPBasicAuth(ACCESS_KEY, SECRET_KEY), headers=headers)
if response.status_code == 200:
    data = response.json()
    print("Success! L-S2-bracket Part Mass Properties:")
    print(json.dumps(data, indent=2))
else:
    print(f"Failed: {response.status_code}")
    print(response.text)
