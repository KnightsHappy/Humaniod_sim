import json
import numpy as np
import scipy.spatial.transform as st

def get_transform_matrix(transform_array):
    T = np.array(transform_array).reshape(4, 4)
    return T

def get_xyz_rpy(T):
    t = T[:3, 3]
    r = st.Rotation.from_matrix(T[:3, :3]).as_euler('xyz')
    return t, r

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
    
    transforms = {}
    for occ in occurrences:
        path = occ.get('path', [])
        path_name = get_path_name(path)
        t = occ.get('transform')
        if not t:
            continue
        T = get_transform_matrix(t)
        
        # We target specific subassemblies of left and right arms
        # Let's check the path suffix
        parts = path_name.split(' -> ')
        if len(parts) == 2:
            parent, child = parts[0], parts[1]
            if 'leftarm' in parent.lower():
                transforms['left_' + child.split(' ')[0]] = T
            elif 'rightarm' in parent.lower():
                transforms['right_' + child.split(' ')[0]] = T

    print("Found Subassembly Transforms:")
    for name, T in transforms.items():
        t, r = get_xyz_rpy(T)
        print(f"  {name}: translation={t}, rotation(rpy)={r}")

    # Let's calculate relative joint origins!
    # Torso origin in base_link (from URDF): [0.150, 0.0, 0.991427]
    torso_origin = np.array([0.150, 0.0, 0.991427])
    T_base_torso = np.eye(4)
    T_base_torso[:3, 3] = torso_origin
    
    print("\n--- LEFT ARM JOINT ORIGINS RELATIVE TO PARENT FRAMES ---")
    
    # Left Joint 1: torso_link -> S1
    if 'left_S1' in transforms:
        T_torso_S1 = np.linalg.inv(T_base_torso) @ transforms['left_S1']
        t, r = get_xyz_rpy(T_torso_S1)
        print(f"left_shoulder_1 (torso_link -> shoulder_link_1_link):")
        print(f"  xyz=\"{t[0]:.6f} {t[1]:.6f} {t[2]:.6f}\" rpy=\"{r[0]:.6f} {r[1]:.6f} {r[2]:.6f}\"")
        
    # Left Joint 2: S1 -> S2
    if 'left_S1' in transforms and 'left_S2' in transforms:
        T_S1_S2 = np.linalg.inv(transforms['left_S1']) @ transforms['left_S2']
        t, r = get_xyz_rpy(T_S1_S2)
        print(f"left_shoulder (shoulder_link_1_link -> shoulder_link_2):")
        print(f"  xyz=\"{t[0]:.6f} {t[1]:.6f} {t[2]:.6f}\" rpy=\"{r[0]:.6f} {r[1]:.6f} {r[2]:.6f}\"")
        
    # Left Joint 3: S2 -> E1
    if 'left_S2' in transforms and 'left_E1' in transforms:
        T_S2_E1 = np.linalg.inv(transforms['left_S2']) @ transforms['left_E1']
        t, r = get_xyz_rpy(T_S2_E1)
        print(f"left_bicep (shoulder_link_2 -> elbow_link_1):")
        print(f"  xyz=\"{t[0]:.6f} {t[1]:.6f} {t[2]:.6f}\" rpy=\"{r[0]:.6f} {r[1]:.6f} {r[2]:.6f}\"")
        
    # Left Joint 4: E1 -> E2
    if 'left_E1' in transforms and 'left_E2' in transforms:
        T_E1_E2 = np.linalg.inv(transforms['left_E1']) @ transforms['left_E2']
        t, r = get_xyz_rpy(T_E1_E2)
        print(f"left_forearm (elbow_link_1 -> elbow_link_2):")
        print(f"  xyz=\"{t[0]:.6f} {t[1]:.6f} {t[2]:.6f}\" rpy=\"{r[0]:.6f} {r[1]:.6f} {r[2]:.6f}\"")

    print("\n--- RIGHT ARM JOINT ORIGINS RELATIVE TO PARENT FRAMES ---")
    
    # Right Joint 1: torso_link -> R-S1
    if 'right_R-S1' in transforms:
        T_torso_RS1 = np.linalg.inv(T_base_torso) @ transforms['right_R-S1']
        t, r = get_xyz_rpy(T_torso_RS1)
        print(f"right_shoulder_1 (torso_link -> right_shoulder_link_1):")
        print(f"  xyz=\"{t[0]:.6f} {t[1]:.6f} {t[2]:.6f}\" rpy=\"{r[0]:.6f} {r[1]:.6f} {r[2]:.6f}\"")
        
    # Right Joint 2: R-S1 -> R-S2
    if 'right_R-S1' in transforms and 'right_R-S2' in transforms:
        T_RS1_RS2 = np.linalg.inv(transforms['right_R-S1']) @ transforms['right_R-S2']
        t, r = get_xyz_rpy(T_RS1_RS2)
        print(f"right_shoulder_2 (right_shoulder_link_1 -> right_shoulder_link_2):")
        print(f"  xyz=\"{t[0]:.6f} {t[1]:.6f} {t[2]:.6f}\" rpy=\"{r[0]:.6f} {r[1]:.6f} {r[2]:.6f}\"")
        
    # Right Joint 3: R-S2 -> R-E1
    if 'right_R-S2' in transforms and 'right_R-E1' in transforms:
        T_RS2_RE1 = np.linalg.inv(transforms['right_R-S2']) @ transforms['right_R-E1']
        t, r = get_xyz_rpy(T_RS2_RE1)
        print(f"right_bicep (right_shoulder_link_2 -> right_elbow_link_1):")
        print(f"  xyz=\"{t[0]:.6f} {t[1]:.6f} {t[2]:.6f}\" rpy=\"{r[0]:.6f} {r[1]:.6f} {r[2]:.6f}\"")
        
    # Right Joint 4: R-E1 -> R-E2
    if 'right_R-E1' in transforms and 'right_R-E2' in transforms:
        T_RE1_RE2 = np.linalg.inv(transforms['right_R-E1']) @ transforms['right_R-E2']
        t, r = get_xyz_rpy(T_RE1_RE2)
        print(f"right_forearm (right_elbow_link_1 -> right_elbow_link_2):")
        print(f"  xyz=\"{t[0]:.6f} {t[1]:.6f} {t[2]:.6f}\" rpy=\"{r[0]:.6f} {r[1]:.6f} {r[2]:.6f}\"")
        
    # Right Joint 5: R-E2 -> R-Wr
    if 'right_R-E2' in transforms and 'right_R-Wr' in transforms:
        T_RE2_RWr = np.linalg.inv(transforms['right_R-E2']) @ transforms['right_R-Wr']
        t, r = get_xyz_rpy(T_RE2_RWr)
        print(f"right_wrist_1 (right_elbow_link_2 -> wrist_link_1):")
        print(f"  xyz=\"{t[0]:.6f} {t[1]:.6f} {t[2]:.6f}\" rpy=\"{r[0]:.6f} {r[1]:.6f} {r[2]:.6f}\"")

if __name__ == '__main__':
    main()
