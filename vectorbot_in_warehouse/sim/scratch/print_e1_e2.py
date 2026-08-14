import json

with open('/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/assembly.json') as f:
    data = json.load(f)

instances = {}
for sa in data.get('subAssemblies', []) + [data.get('rootAssembly', {})]:
    for inst in sa.get('instances', []):
        instances[inst['id']] = inst

def get_path_name(path):
    names = []
    for inst_id in path:
        inst = instances.get(inst_id)
        if inst:
            names.append(inst['name'])
        else:
            names.append(inst_id)
    return " -> ".join(names)

print("E1 Assembly occurrences:")
for occ in data.get('rootAssembly', {}).get('occurrences', []):
    path = occ.get('path', [])
    path_name = get_path_name(path)
    if "E1 <1>" in path_name and len(path) > 1:
        leaf_inst = instances.get(path[-1])
        leaf_name = leaf_inst['name'] if leaf_inst else path[-1]
        transform = occ.get('transform')
        if transform:
            trans = [transform[3], transform[7], transform[11]]
            print(f"  {leaf_name:<40} | translation: {trans}")

print("\nE2 Assembly occurrences:")
for occ in data.get('rootAssembly', {}).get('occurrences', []):
    path = occ.get('path', [])
    path_name = get_path_name(path)
    if "E2 <1>" in path_name and len(path) > 1:
        leaf_inst = instances.get(path[-1])
        leaf_name = leaf_inst['name'] if leaf_inst else path[-1]
        transform = occ.get('transform')
        if transform:
            trans = [transform[3], transform[7], transform[11]]
            print(f"  {leaf_name:<40} | translation: {trans}")
