import numpy as np

def main():
    # Torso origin in base_link frame
    torso_origin = np.array([0.150, 0.0, 0.991427])

    # Absolute CAD coordinates of the right arm joints
    P_J1 = np.array([0.19182396, 0.05236644, 1.02210082])
    P_J2 = np.array([0.214974, 0.113366, 1.0221])
    P_J3 = np.array([0.191824, 0.113366, 0.9691])
    P_J4 = np.array([0.295467, 0.072677, 0.7404])
    P_J5 = np.array([0.33265652, 0.18925593, 1.36304832])
    P_J6 = np.array([0.33096728, 0.16768111, 1.44875012])

    print("Relative joint origins:")
    
    # Joint 1: torso_link -> right_shoulder_link_1
    xyz_J1 = P_J1 - torso_origin
    print(f"Joint 1 (right_shoulder_1): xyz=\"{xyz_J1[0]:.6f} {xyz_J1[1]:.6f} {xyz_J1[2]:.6f}\"")

    # Joint 2: right_shoulder_link_1 -> right_shoulder_link_2
    xyz_J2 = P_J2 - P_J1
    print(f"Joint 2 (right_shoulder_2): xyz=\"{xyz_J2[0]:.6f} {xyz_J2[1]:.6f} {xyz_J2[2]:.6f}\"")

    # Joint 3: right_shoulder_link_2 -> right_elbow_link_1
    xyz_J3 = P_J3 - P_J2
    print(f"Joint 3 (right_bicep): xyz=\"{xyz_J3[0]:.6f} {xyz_J3[1]:.6f} {xyz_J3[2]:.6f}\"")

    # Joint 4: right_elbow_link_1 -> right_elbow_link_2
    xyz_J4 = P_J4 - P_J3
    print(f"Joint 4 (right_forearm): xyz=\"{xyz_J4[0]:.6f} {xyz_J4[1]:.6f} {xyz_J4[2]:.6f}\"")

    # Joint 5: right_elbow_link_2 -> wrist_link_1
    xyz_J5 = P_J5 - P_J4
    print(f"Joint 5 (right_wrist_1): xyz=\"{xyz_J5[0]:.6f} {xyz_J5[1]:.6f} {xyz_J5[2]:.6f}\"")

    # Joint 6: wrist_link_1 -> ee_link
    xyz_J6 = P_J6 - P_J5
    print(f"Joint 6 (right_wrist_2): xyz=\"{xyz_J6[0]:.6f} {xyz_J6[1]:.6f} {xyz_J6[2]:.6f}\"")

if __name__ == '__main__':
    main()
