import json

def main():
    json_path = '/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/assembly.json'
    with open(json_path) as f:
        data = json.load(f)

    occurrences = data.get('rootAssembly', {}).get('occurrences', [])
    print(f"Total occurrences: {len(occurrences)}")
    for i, occ in enumerate(occurrences[:15]):
        print(f"\nOccurrence {i}:")
        print(f"  Path: {occ.get('path')}")
        print(f"  Has Transform: {'transform' in occ}")
        if 'transform' in occ:
            print(f"  Transform: {occ['transform']}")

if __name__ == '__main__':
    main()
