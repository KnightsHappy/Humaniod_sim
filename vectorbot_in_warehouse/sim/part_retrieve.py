import requests
from requests.auth import HTTPBasicAuth
import re
from collections import Counter

# 1. Setup your credentials and document details
ACCESS_KEY = "on_ZBYH1toFedwHtBWhgI1wX"
SECRET_KEY = "v8l3gYHedapodnDXImXq9NpztNIWOQ9lD8AWpIHryHeZu95S"

# Replace these with your actual URL IDs
DID = "c6f6216d8062a2927a42dbbe"
WID = "d0059b9eedacc9158e955397"
EID = "90e7b5777f61e72dfddbc835"

# 2. Build the API target (General Assembly Definition)
url = f"https://cad.onshape.com/api/v1/assemblies/d/{DID}/w/{WID}/e/{EID}"

headers = {
    "Accept": "application/json; charset=UTF-8",
    "Content-Type": "application/json"
}

# 3. Make the request
response = requests.get(url, auth=HTTPBasicAuth(ACCESS_KEY, SECRET_KEY), headers=headers)

def clean_part_name(name):
    # Strip instance suffixes like <1> or (1) at the end of the name
    name = re.sub(r'\s*[<(]\d+[>)]\s*$', '', name)
    return name.strip()

if response.status_code == 200:
    data = response.json()
    
    # Map assemblies by elementId for fast lookup
    assemblies = {}
    root = data.get('rootAssembly', {})
    assemblies[root['elementId']] = root
    for sa in data.get('subAssemblies', []):
        assemblies[sa['elementId']] = sa

    # --- 1. Print Hierarchical Tree ---
    print("\n==================================================================")
    print("                    ASSEMBLY STRUCTURE HIERARCHY")
    print("==================================================================")
    
    def print_assembly_tree(element_id, name, indent=''):
        assembly = assemblies.get(element_id)
        if not assembly:
            print(f"{indent}- {name} (Assembly details not found)")
            return
        
        # If the assembly itself is suppressed, don't show it or its components
        if assembly.get('suppressed'):
            return
            
        print(f"{indent}+ {name}")
        for inst in assembly.get('instances', []):
            if inst.get('suppressed'):
                continue
                
            inst_name = inst.get('name', 'Unknown')
            inst_type = inst.get('type')
            
            if inst_type == 'Part':
                print(f"{indent}  - {inst_name}")
            elif inst_type == 'Assembly':
                print_assembly_tree(inst.get('elementId'), inst_name, indent + '  ')

    print_assembly_tree(root['elementId'], root.get('name', 'Root Assembly'))

    # --- 2. Print Flattened Summary of Parts ---
    print("\n==================================================================")
    print("                     FLATTENED PARTS SUMMARY")
    print("==================================================================")
    
    active_parts = []
    for occ in root.get('occurrences', []):
        path = occ.get('path', [])
        current_assembly = root
        has_suppressed = False
        leaf_instance = None
        
        for i, inst_id in enumerate(path):
            inst = next((x for x in current_assembly.get('instances', []) if x['id'] == inst_id), None)
            if not inst:
                break
            if inst.get('suppressed'):
                has_suppressed = True
                break
            
            if i == len(path) - 1:
                leaf_instance = inst
            else:
                if inst.get('type') == 'Assembly':
                    current_assembly = assemblies.get(inst['elementId'])
                    if not current_assembly:
                        break
        
        if not has_suppressed and leaf_instance and leaf_instance.get('type') == 'Part':
            active_parts.append(leaf_instance)

    # Clean and count the parts
    cleaned_names = [clean_part_name(p['name']) for p in active_parts]
    counts = Counter(cleaned_names)
    
    print(f"{'Part Name':<50} | {'Qty':<5}")
    print("-" * 58)
    for part_name, qty in sorted(counts.items()):
        print(f"{part_name:<50} | {qty:<5}")

else:
    print(f"Failed to fetch data. Error {response.status_code}: {response.text}")