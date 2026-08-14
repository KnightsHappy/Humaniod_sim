import numpy as np

def main():
    # Symmetry plane: X_mid = -0.115176
    X_mid = -0.115176
    
    def mirror_point(p):
        return np.array([2 * X_mid - p[0], p[1], p[2]])

    # Left arm joint positions relative to torso_link
    left_joints = {
        'J1': np.array([-0.272176, 0.052366, 0.030673]),
        'J2': np.array([-0.272176 - 0.02315, 0.052366 + 0.061, 0.030673]),
        'J3': np.array([-0.272176 - 0.02315 - 0.066615, 0.052366 + 0.061 - 0.065012, 0.030673 - 0.053]),
        'J4': np.array([-0.272176 - 0.02315 - 0.066615 - 0.013878, 0.052366 + 0.061 - 0.065012 + 0.024323, 0.030673 - 0.053 - 0.2287])
    }

    print("Left Arm absolute joint positions (relative to torso):")
    for name, p in left_joints.items():
        print(f"  {name}: {p}")

    print("\nMirrored Right Arm absolute joint positions:")
    right_joints_expected = {}
    for name, p in left_joints.items():
        right_joints_expected[name] = mirror_point(p)
        print(f"  {name}: {right_joints_expected[name]}")

    # Right arm relative joint origins in our proposed configuration:
    # right_shoulder_1: [0.041824, 0.052366, 0.030673]
    # right_shoulder_2: [0.023150, 0.061000, 0.0]
    # right_bicep: [0.066615, -0.065012, -0.053]
    # right_forearm: [0.013878, 0.024323, -0.2287]
    
    right_J1 = np.array([0.041824, 0.052366, 0.030673])
    right_J2 = right_J1 + np.array([0.023150, 0.061000, 0.0])
    right_J3 = right_J2 + np.array([0.066615, -0.065012, -0.053])
    right_J4 = right_J3 + np.array([0.013878, 0.024323, -0.2287])

    print("\nProposed Right Arm absolute joint positions:")
    print(f"  J1: {right_J1}")
    print(f"  J2: {right_J2}")
    print(f"  J3: {right_J3}")
    print(f"  J4: {right_J4}")

    print("\nProposed vs Expected Differences:")
    print(f"  J1 diff: {right_J1 - right_joints_expected['J1']}")
    print(f"  J2 diff: {right_J2 - right_joints_expected['J2']}")
    print(f"  J3 diff: {right_J3 - right_joints_expected['J3']}")
    print(f"  J4 diff: {right_J4 - right_joints_expected['J4']}")

if __name__ == '__main__':
    main()
