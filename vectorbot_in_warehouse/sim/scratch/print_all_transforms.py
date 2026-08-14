import json

def main():
    json_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/assembly.json'
    with open(json_path) as f:
        data = json.load(f)

    # Build instance map
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

    occurrences = data.get('rootAssembly', {}).get('occurrences', [])
    for occ in occurrences:
        path = occ.get('path', [])
        path_name = get_path_name(path)
        # If the path name contains rightarm or leftarm, print it
        if 'leftarm' in path_name.lower() or 'rightarm' in path_name.lower():
            if len(path) <= 3: # Keep it short
                print(f"Path: {path_name}")
                print(f"  Transform: {occ.get('transform')}")

if __name__ == '__main__':
    main()
