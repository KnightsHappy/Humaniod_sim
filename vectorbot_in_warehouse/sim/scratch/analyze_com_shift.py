import xml.etree.ElementTree as ET
import numpy as np

def rpy_to_R(rpy):
    r, p, y = rpy
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(r), -np.sin(r)],
        [0, np.sin(r), np.cos(r)]
    ])
    Ry = np.array([
        [np.cos(p), 0, np.sin(p)],
        [0, 1, 0],
        [-np.sin(p), 0, np.cos(p)]
    ])
    Rz = np.array([
        [np.cos(y), -np.sin(y), 0],
        [np.sin(y), np.cos(y), 0],
        [0, 0, 1]
    ])
    return Rz @ (Ry @ Rx)

def get_transform(xyz, rpy):
    R = rpy_to_R(rpy)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = xyz
    return T

def run_analysis(base_mass):
    urdf_path = "/home/nihit/bots/vectorbot_in_warehouse/sim/scratch/temp_vector.urdf"
    tree = ET.parse(urdf_path)
    root = tree.getroot()

    # Parse links
    links = {}
    for link in root.findall("link"):
        name = link.get("name")
        inertial = link.find("inertial")
        if inertial is not None:
            mass_el = inertial.find("mass")
            if name == "base_link":
                mass = base_mass
            else:
                mass = float(mass_el.get("value")) if mass_el is not None else 0.0
            
            origin = inertial.find("origin")
            xyz = np.zeros(3)
            rpy = np.zeros(3)
            if origin is not None:
                xyz_str = origin.get("xyz")
                if xyz_str:
                    xyz = np.array([float(x) for x in xyz_str.split()])
                rpy_str = origin.get("rpy")
                if rpy_str:
                    rpy = np.array([float(x) for x in rpy_str.split()])
            links[name] = {"mass": mass, "com_local": xyz, "com_rpy": rpy}
        else:
            links[name] = {"mass": 0.0, "com_local": np.zeros(3), "com_rpy": np.zeros(3)}

    # Parse joints
    joints = {}
    for joint in root.findall("joint"):
        name = joint.get("name")
        parent = joint.find("parent").get("link")
        child = joint.find("child").get("link")
        
        origin = joint.find("origin")
        xyz = np.zeros(3)
        rpy = np.zeros(3)
        if origin is not None:
            xyz_str = origin.get("xyz")
            if xyz_str:
                xyz = np.array([float(x) for x in xyz_str.split()])
            rpy_str = origin.get("rpy")
            if rpy_str:
                rpy = np.array([float(x) for x in rpy_str.split()])
        
        joints[child] = {"parent": parent, "xyz": xyz, "rpy": rpy}

    # Compute transforms relative to base_link
    link_transforms = {"base_link": np.eye(4)}
    
    def get_link_transform(link_name):
        if link_name in link_transforms:
            return link_transforms[link_name]
        if link_name not in joints:
            link_transforms[link_name] = np.eye(4)
            return link_transforms[link_name]
        joint_info = joints[link_name]
        parent = joint_info["parent"]
        T_parent = get_link_transform(parent)
        T_joint = get_transform(joint_info["xyz"], joint_info["rpy"])
        T_link = T_parent @ T_joint
        link_transforms[link_name] = T_link
        return T_link

    total_mass = 0.0
    weighted_com = np.zeros(3)
    
    for link_name in links:
        get_link_transform(link_name)
        
    for link_name, info in links.items():
        mass = info["mass"]
        if mass <= 0.0:
            continue
        T_link = link_transforms[link_name]
        com_local = info["com_local"]
        com_local_hom = np.append(com_local, 1.0)
        com_global = (T_link @ com_local_hom)[:3]
        total_mass += mass
        weighted_com += mass * com_global
        
    return total_mass, weighted_com / total_mass

def main():
    print(f"{'Base Mass (kg)':<15} | {'Total Mass (kg)':<15} | {'COM x (m)':<10} | {'COM y (m)':<10} | {'COM z (m)':<10}")
    print("-" * 70)
    for bm in [66.476139, 100.0, 150.0, 200.0, 300.0, 500.0, 1000.0]:
        tm, com = run_analysis(bm)
        print(f"{bm:<15.4f} | {tm:<15.4f} | {com[0]:<10.6f} | {com[1]:<10.6f} | {com[2]:<10.6f}")

if __name__ == "__main__":
    main()
