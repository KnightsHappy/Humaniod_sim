import json
import numpy as np

def main():
    json_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/assembly.json'
    with open(json_path) as f:
        data = json.load(f)

    # Build instance map
    instances = {}
    for sa in data.get('subAssemblies', []) + [data.get('rootAssembly', {})]:
        for inst in sa.get('instances', []):
            instances[inst['id']] = inst

    # Helper to get full path name
    def get_path_name(path):
        names = []
        for inst_id in path:
            inst = instances.get(inst_id)
            if inst:
                names.append(inst['name'])
            else:
                names.append(inst_id)
        return " -> ".join(names)

    print("Searching right arm and base parts...")
    occurrences = data.get('rootAssembly', {}).get('occurrences', [])
    
    parsed_occurrences = []
    
    for occ in occurrences:
        path = occ.get('path', [])
        path_name = get_path_name(path)
        transform = occ.get('transform')
        if not transform:
            continue
            
        # Parse 4x4 row-major matrix:
        t = [transform[3], transform[7], transform[11]]
        
        info = {
            'path_name': path_name,
            'translation': t,
            'matrix': transform
        }
        parsed_occurrences.append(info)

    def find_and_print(parts_list, name_contains, subassembly_contains=None):
        print(f"\nLooking for parts matching '{name_contains}' under '{subassembly_contains}':")
        matched = 0
        for p in parts_list:
            path_name = p['path_name']
            if name_contains.lower() in path_name.lower():
                if subassembly_contains is None or subassembly_contains.lower() in path_name.lower():
                    print(f"  {path_name}:")
                    print(f"    Translation: {p['translation']}")
                    matched += 1
        if matched == 0:
            print("  No match found!")

    find_and_print(parsed_occurrences, 'ID-Needle-AXK-3047', 'R-Base')
    find_and_print(parsed_occurrences, 'L-S2-bracket', 'R-S1')
    find_and_print(parsed_occurrences, 'L-S2-Motor-supporting-bracket-Mirrored', 'R-S2')
    find_and_print(parsed_occurrences, 'ID-Needle-AXK-3047', 'R-S2')
    find_and_print(parsed_occurrences, 'L-E1-motor-bracket', 'R-E1')
    find_and_print(parsed_occurrences, 'L-E2-motorholding-bracket-Mirrored', 'R-E2')
    find_and_print(parsed_occurrences, 'ID-Needle-AXK-3047', 'R-E2')
    find_and_print(parsed_occurrences, 'L-Wp-1-motorholding-bracket-Mirrored', 'R-Wr')
    find_and_print(parsed_occurrences, 'RDS5160', 'R-Wr')
    find_and_print(parsed_occurrences, 'R-Hand-EE')

if __name__ == '__main__':
    main()
