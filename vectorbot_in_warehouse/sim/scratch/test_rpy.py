import numpy as np

# R-Hand-EE transform matrix from Onshape
T = np.array([
    [0.999254075443207, 0.03515289107545025, -0.0159864617466982],
    [0.034614845998456004, -0.998863263775754, -0.032771828080710004],
    [-0.017120313859397798, 0.032194013857951446, -0.999334999049403]
])

# Compute Euler angles (RPY)
# We assume standard ROS rotation ordering: Rz(yaw) * Ry(pitch) * Rx(roll)
# pitch = atan2(-T[2,0], sqrt(T[2,1]^2 + T[2,2]^2))
# if pitch is close to pi/2 or -pi/2, it's gimbal lock.
# Otherwise:
# roll = atan2(T[2,1], T[2,2])
# yaw = atan2(T[1,0], T[0,0])

pitch = np.arctan2(-T[2,0], np.sqrt(T[2,1]**2 + T[2,2]**2))
roll = np.arctan2(T[2,1], T[2,2])
yaw = np.arctan2(T[1,0], T[0,0])

print(f"Calculated RPY: {roll} {pitch} {yaw}")
print(f"Xacro visual RPY: 3.10939 0.0171212 0.0346268")
