import xml.etree.ElementTree as ET
import os

urdf_path = "/home/nihit/bots/Assembly_mass_replace/assembly_1_1/urdf/assembly_1_1.urdf"
xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"

# Parse URDF
tree_urdf = ET.parse(urdf_path)
root_urdf = tree_urdf.getroot()

urdf_info = {}
for link in root_urdf.findall('link'):
    name = link.get('name')
    inertial = link.find('inertial')
    meshes = []
    for visual in link.findall('visual'):
        geom = visual.find('geometry')
        if geom is not None:
            mesh = geom.find('mesh')
            if mesh is not None:
                fn = mesh.get('filename')
                meshes.append(os.path.basename(fn))
    
    # Store inertial details
    inertial_data = None
    if inertial is not None:
        mass = inertial.find('mass')
        mass_val = float(mass.get('value')) if mass is not None else None
        origin = inertial.find('origin')
        xyz = origin.get('xyz') if origin is not None else None
        rpy = origin.get('rpy') if origin is not None else None
        inertia = inertial.find('inertia')
        inertia_vals = {k: float(inertia.get(k)) for k in ['ixx', 'ixy', 'ixz', 'iyy', 'iyz', 'izz']} if inertia is not None else {}
        inertial_data = {
            'mass': mass_val,
            'xyz': xyz,
            'rpy': rpy,
            'inertia': inertia_vals
        }
    
    urdf_info[name] = {
        'meshes': meshes,
        'inertial': inertial_data
    }

# Parse XACRO
tree_xacro = ET.parse(xacro_path)
root_xacro = tree_xacro.getroot()

xacro_info = {}
for elem in root_xacro.iter():
    if elem.tag == 'link' or elem.tag.endswith('link'):
        name = elem.get('name')
        inertial = elem.find('inertial')
        meshes = []
        for visual in elem.findall('visual'):
            geom = visual.find('geometry')
            if geom is not None:
                mesh = geom.find('mesh')
                if mesh is not None:
                    fn = mesh.get('filename')
                    meshes.append(os.path.basename(fn))
        
        # Store inertial details
        inertial_data = None
        if inertial is not None:
            mass = inertial.find('mass')
            mass_val = float(mass.get('value')) if mass is not None else None
            origin = inertial.find('origin')
            xyz = origin.get('xyz') if origin is not None else None
            rpy = origin.get('rpy') if origin is not None else None
            inertia = inertial.find('inertia')
            inertia_vals = {k: float(inertia.get(k)) for k in ['ixx', 'ixy', 'ixz', 'iyy', 'iyz', 'izz']} if inertia is not None else {}
            inertial_data = {
                'mass': mass_val,
                'xyz': xyz,
                'rpy': rpy,
                'inertia': inertia_vals
            }
        
        xacro_info[name] = {
            'meshes': meshes,
            'inertial': inertial_data
        }

print("=== URDF LINK INFO ===")
for name, data in urdf_info.items():
    print(f"Link: {name}")
    print(f"  Meshes ({len(data['meshes'])}): {data['meshes'][:5]} ...")
    if data['inertial']:
        print(f"  Inertial: Mass: {data['inertial']['mass']}, XYZ: {data['inertial']['xyz']}")
    else:
        print("  Inertial: None")

print("\n=== XACRO LINK INFO ===")
for name, data in xacro_info.items():
    print(f"Link: {name}")
    print(f"  Meshes ({len(data['meshes'])}): {data['meshes'][:5]} ...")
    if data['inertial']:
        print(f"  Inertial: Mass: {data['inertial']['mass']}, XYZ: {data['inertial']['xyz']}")
    else:
        print("  Inertial: None")
