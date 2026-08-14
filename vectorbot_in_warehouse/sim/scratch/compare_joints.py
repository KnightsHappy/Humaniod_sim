import xml.etree.ElementTree as ET

urdf_path = "/home/nihit/bots/Assembly_mass_replace/assembly_1_1/urdf/assembly_1_1.urdf"
xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"

tree_urdf = ET.parse(urdf_path)
root_urdf = tree_urdf.getroot()

tree_xacro = ET.parse(xacro_path)
root_xacro = tree_xacro.getroot()

print("=== Gearbox / Wheel Joints in URDF ===")
for joint in root_urdf.findall('joint'):
    if 'gearbox' in joint.get('name') or 'revolute' in joint.get('name'):
        child = joint.find('child').get('link')
        if 'gearbox' in child or 'part_1' in child:
            origin = joint.find('origin')
            xyz = origin.get('xyz') if origin is not None else "0 0 0"
            rpy = origin.get('rpy') if origin is not None else "0 0 0"
            print(f"Joint: {joint.get('name')} | Parent: {joint.find('parent').get('link')} | Child: {child}")
            print(f"  xyz: {xyz}, rpy: {rpy}")

print("\n=== Gearbox / Wheel Joints in Xacro ===")
for joint in root_xacro.findall('.//joint'):
    child = joint.find('child').get('link')
    if 'gearbox' in child or 'wheel' in child:
        origin = joint.find('origin')
        xyz = origin.get('xyz') if origin is not None else "0 0 0"
        rpy = origin.get('rpy') if origin is not None else "0 0 0"
        print(f"Joint: {joint.get('name')} | Parent: {joint.find('parent').get('link')} | Child: {child}")
        print(f"  xyz: {xyz}, rpy: {rpy}")
