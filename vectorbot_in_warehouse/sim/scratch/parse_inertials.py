import xml.etree.ElementTree as ET

urdf_path = "/home/nihit/bots/Assembly_mass_replace/assembly_1_1/urdf/assembly_1_1.urdf"
xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"

# Parse URDF
tree_urdf = ET.parse(urdf_path)
root_urdf = tree_urdf.getroot()

print("=== ALL URDF LINKS WITH INERTIALS ===")
for link in root_urdf.findall('link'):
    name = link.get('name')
    inertial = link.find('inertial')
    if inertial is not None:
        mass = inertial.find('mass')
        mass_val = mass.get('value') if mass is not None else None
        origin = inertial.find('origin')
        xyz = origin.get('xyz') if origin is not None else None
        rpy = origin.get('rpy') if origin is not None else None
        inertia = inertial.find('inertia')
        inertia_vals = {k: inertia.get(k) for k in ['ixx', 'ixy', 'ixz', 'iyy', 'iyz', 'izz']} if inertia is not None else {}
        print(f"URDF Link: {name}")
        print(f"  Mass: {mass_val}")
        print(f"  Origin xyz: {xyz}, rpy: {rpy}")
        print(f"  Inertia: {inertia_vals}")

print("\n=== ALL XACRO LINKS WITH INERTIALS (XML PARSED) ===")
try:
    tree_xacro = ET.parse(xacro_path)
    root_xacro = tree_xacro.getroot()
    # Find all elements that might be links or contain inertial
    for elem in root_xacro.iter():
        if elem.tag == 'link' or elem.tag.endswith('link'):
            inertial = elem.find('inertial')
            if inertial is not None:
                name = elem.get('name')
                mass = inertial.find('mass')
                mass_val = mass.get('value') if mass is not None else None
                origin = inertial.find('origin')
                xyz = origin.get('xyz') if origin is not None else None
                rpy = origin.get('rpy') if origin is not None else None
                inertia = inertial.find('inertia')
                inertia_vals = {k: inertia.get(k) for k in ['ixx', 'ixy', 'ixz', 'iyy', 'iyz', 'izz']} if inertia is not None else {}
                print(f"Xacro Link: {name}")
                print(f"  Mass: {mass_val}")
                print(f"  Origin xyz: {xyz}, rpy: {rpy}")
                print(f"  Inertia: {inertia_vals}")
except Exception as e:
    print(f"Could not parse xacro as standard XML: {e}")
