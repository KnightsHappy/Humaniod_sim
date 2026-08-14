import json

with open('/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/assembly.json') as f:
    data = json.load(f)

root_assembly = data.get('rootAssembly', {})
mates = root_assembly.get('mates', [])
mate_features = root_assembly.get('mateFeatures', [])

print(f"Number of mates: {len(mates)}")
print(f"Number of mateFeatures: {len(mate_features)}")

# Let's inspect mateFeatures
for i, feature in enumerate(mate_features):
    feature_type = feature.get('featureSpec', {}).get('featureTypeName', 'unknown')
    name = feature.get('name', '')
    print(f"\nFeature {i}: {name} ({feature_type})")
    # print some details of the feature spec
    spec = feature.get('featureSpec', {})
    parameters = spec.get('parameters', [])
    for p in parameters:
        pid = p.get('parameterId')
        # print parameter details
        if pid in ['mateConnectors', 'mateType']:
            print(f"  {pid}: {p}")

# Let's also check if sub-assemblies have mates
for sa in data.get('subAssemblies', []):
    print(f"\nSub-assembly {sa.get('displayName')} / {sa.get('elementId')}:")
    print(f"  Mates: {len(sa.get('mates', []))}")
    print(f"  MateFeatures: {len(sa.get('mateFeatures', []))}")
    for feature in sa.get('mateFeatures', []):
        print(f"    MateFeature: {feature.get('name')}")
