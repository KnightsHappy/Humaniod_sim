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
    
    # Map subassemblies by elementId
    sub_assemblies = {}
    for sa in data.get('subAssemblies', []):
        sub_assemblies[sa['elementId']] = sa
        
    out_lines = []
    def print_sa_structure(element_id, name, indent=''):
        sa = sub_assemblies.get(element_id)
        if not sa:
            out_lines.append(f"{indent}+ {name} (Details not in main API response)")
            return
        
        out_lines.append(f"{indent}+ {name} (elementId: {element_id})")
        for inst in sa.get('instances', []):
            if inst.get('suppressed'):
                continue
            inst_name = inst.get('name', 'Unknown')
            inst_type = inst.get('type')
            inst_eid = inst.get('elementId')
            
            if inst_type == 'Part':
                out_lines.append(f"{indent}  - Part: {inst_name} (elementId: {inst_eid}, partId: {inst.get('partId')})")
            elif inst_type == 'Assembly':
                print_sa_structure(inst_eid, inst_name, indent + '  ')

    out_lines.append("=== LEFT ARM SUBASSEMBLY STRUCTURE ===")
    print_sa_structure("d7bfc538cfce4fda6e46f3f6", "URDF-ID-leftarm")
    
    out_lines.append("\n=== RIGHT ARM SUBASSEMBLY STRUCTURE ===")
    print_sa_structure("5fdb80877b4679df0a09763a", "URDF-ID-rightarm")
    
    with open("/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/arms_structure.txt", "w") as f:
        f.write("\n".join(out_lines))
    print("Full structure written to scratch/arms_structure.txt")
else:
    print("Failed to fetch")
