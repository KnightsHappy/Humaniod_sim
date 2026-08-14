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
    
    print("Left Arm Key Parts:")
    for occ in occurrences:
        path = occ.get('path', [])
        path_name = get_path_name(path)
        if 'leftarm' in path_name.lower():
            if 'needle' in path_name.lower() or 'bearing_holder' in path_name.lower():
                t = occ.get('transform')
                if t:
                    print(f"  {path_name}: {[t[3], t[7], t[11]]}")
                    
    print("\nRight Arm Key Parts:")
    for occ in occurrences:
        path = occ.get('path', [])
        path_name = get_path_name(path)
        if 'rightarm' in path_name.lower():
            if 'needle' in path_name.lower() or 'bearing_holder' in path_name.lower():
                t = occ.get('transform')
                if t:
                    print(f"  {path_name}: {[t[3], t[7], t[11]]}")

if __name__ == '__main__':
    main()
