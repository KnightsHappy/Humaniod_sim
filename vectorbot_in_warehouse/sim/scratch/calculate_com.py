import xml.etree.ElementTree as ET
import numpy as np

xacro_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/vector_description/urdf/vector.xacro"

# Let's define the joint origins to compute the frame offsets relative to base_link
joint_origins = {
    "base_link": np.array([0.0, 0.0, 0.0]),
    "torso_link": np.array([0.150000, 0.000000, 0.991427]),
    "shoulder_link_1_link": np.array([-0.122176, 0.052366, 1.022100]),
    "shoulder_link_2": np.array([-0.145326, 0.113366, 1.022100]),
    "elbow_link_1": np.array([-0.211941, 0.048354, 0.969100]),
    "elbow_link_2": np.array([-0.225819, 0.072677, 0.740400]),
    "right_shoulder_link_1": np.array([0.191824, 0.052366, 1.022101]),
    "right_shoulder_link_2": np.array([0.214974, 0.113366, 1.022100]),
    "right_elbow_link_1": np.array([0.281589, 0.048354, 0.969100]),
    "right_elbow_link_2": np.array([0.295467, 0.072677, 0.740400]),
    "wrist_link_1": np.array([0.332657, 0.189256, 1.363048]),
    "ee_link": np.array([0.330968, 0.167681, 1.448750])
}

# Old masses and origins (before our update)
old_data = {
    "base_link": {"mass": 25.0, "xyz": [0.0488, 0.0656, 0.2]},
    "torso_link": {"mass": 15.0, "xyz": [-0.101200, 0.065600, -0.041427]},
    "shoulder_link_1_link": {"mass": 0.115753, "xyz": [-0.031388, -0.0363689, 5.57414e-18]},
    "shoulder_link_2": {"mass": 0.072948, "xyz": [0.00862267, -9.64508e-06, 0.0263137]},
    "elbow_link_1": {"mass": 2.0, "xyz": [0.0, 0.0, 0.0]},
    "elbow_link_2": {"mass": 2.0, "xyz": [0.0, 0.0, 0.0]},
    "right_shoulder_link_1": {"mass": 0.115753, "xyz": [-0.031388, 0.0363689, 5.57414e-18]},
    "right_shoulder_link_2": {"mass": 0.072948, "xyz": [0.00862267, 9.64508e-06, 0.0263137]},
    "right_elbow_link_1": {"mass": 2.0, "xyz": [0.0, 0.0, 0.0]},
    "right_elbow_link_2": {"mass": 2.0, "xyz": [0.0, 0.0, 0.0]},
    "wrist_link_1": {"mass": 2.0, "xyz": [0.0, 0.0, 0.0]},
    "ee_link": {"mass": 2.0, "xyz": [0.0, 0.0, 0.0]}
}

# Parse current xacro
tree = ET.parse(xacro_path)
root = tree.getroot()

current_data = {}
for link in root.findall('.//link'):
    name = link.get('name')
    if name in joint_origins:
        inertial = link.find('inertial')
        if inertial is not None:
            mass_val = float(inertial.find('mass').get('value'))
            origin = inertial.find('origin')
            xyz_str = origin.get('xyz') if origin is not None else "0 0 0"
            xyz = [float(x) for x in xyz_str.split()]
            current_data[name] = {"mass": mass_val, "xyz": xyz}

def compute_com(dataset):
    total_mass = 0.0
    weighted_xyz = np.zeros(3)
    
    for name, info in dataset.items():
        m = info["mass"]
        local_xyz = np.array(info["xyz"])
        # Global position of link COM
        global_xyz = joint_origins[name] + local_xyz
        
        total_mass += m
        weighted_xyz += m * global_xyz
        
    return total_mass, weighted_xyz / total_mass

old_mass, old_com = compute_com(old_data)
curr_mass, curr_com = compute_com(current_data)

print("OLD CONFIGURATION:")
print(f"  Total mass: {old_mass:.4f} kg")
print(f"  COM xyz:    {old_com}")
print("\nCURRENT CONFIGURATION:")
print(f"  Total mass: {curr_mass:.4f} kg")
print(f"  COM xyz:    {curr_com}")
print("\nSHIFT (Current - Old):")
print(f"  d_xyz:      {curr_com - old_com}")
print(f"  d_mass:     {curr_mass - old_mass:.4f} kg")
