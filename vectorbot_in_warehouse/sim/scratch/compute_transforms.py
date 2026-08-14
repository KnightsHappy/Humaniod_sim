import numpy as np
import scipy.spatial.transform as st

def get_transform(xyz, rpy):
    t = np.array(xyz)
    r = st.Rotation.from_euler('xyz', rpy).as_matrix()
    T = np.eye(4)
    T[:3, :3] = r
    T[:3, 3] = t
    return T

def get_xyz_rpy(T):
    t = T[:3, 3]
    r = st.Rotation.from_matrix(T[:3, :3]).as_euler('xyz')
    return t, r

# T1: root -> part_1
T_root_part1 = get_transform([0.269068, 0.134455, -0.0890278], [0, 0, -1.5708])
# T2: part_1 -> gearbox
T_part1_gearbox = get_transform([0, 0.0185, 0], [np.pi, 0, np.pi])

# We want: root -> gearbox -> right_wheel_link
# Originally: root -> part_1 -> gearbox
# So: T_root_gearbox = T_root_part1 * T_part1_gearbox
T_root_gearbox = T_root_part1 @ T_part1_gearbox

# And right_wheel_link is part_1, so:
# T_gearbox_wheel = T_gearbox_root * T_root_part1 = T_part1_gearbox^-1
T_gearbox_wheel = np.linalg.inv(T_part1_gearbox)

print("T_root_gearbox:")
xyz, rpy = get_xyz_rpy(T_root_gearbox)
print(f"  xyz: {xyz}")
print(f"  rpy: {rpy}")

print("\nT_gearbox_wheel:")
xyz, rpy = get_xyz_rpy(T_gearbox_wheel)
print(f"  xyz: {xyz}")
print(f"  rpy: {rpy}")
