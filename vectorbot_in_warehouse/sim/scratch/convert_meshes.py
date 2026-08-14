import numpy as np

# World coordinates of link frames
P_torso_link = np.array([0.15, 0.0, 0.991427])
P_needle_left = np.array([-0.23713309, 0.13395599, 0.66024135])
P_ee_left = np.array([-0.07995601, 0.23873828, 0.56293812])

# Mesh translation offsets:
offset_wrist = P_torso_link - P_needle_left
offset_ee = P_torso_link - P_ee_left

print(f"offset_wrist: {offset_wrist}")
print(f"offset_ee: {offset_ee}")

print("\n--- Mesh conversions for left_wrist_link_1 ---")
wrist_meshes = [
    ("L_Wp_1_motorholding_bracket.stl", [-0.378135, 0.074362, -0.249484], "0.101897 -0.629318 1.58692", "0.768627_0.886275_0.952941_0.000000_0.000000"),
    ("L_Wp_2_cover.stl", [-0.378137, 0.074523, -0.249367], "0.101897 -0.629318 1.58692", "0.917647_0.917647_0.917647_0.000000_0.000000"),
    ("L_Wp_1_cover.stl", [-0.378137, 0.074523, -0.249367], "0.101897 -0.629318 1.58692", "0.917647_0.917647_0.917647_0.000000_0.000000"),
    ("L_Wp_motor_3dp_piece.stl", [-0.378135, 0.074362, -0.249484], "0.101897 -0.629318 1.58692", "0.972549_0.529412_0.003922_0.000000_0.000000"),
    ("L_Wp_2_motorholding_bracket.stl", [-0.378135, 0.074362, -0.249484], "0.101897 -0.629318 1.58692", "0.498039_0.498039_0.498039_0.000000_0.000000"),
    ("RDS5160_v39_1.stl", [-0.420630, 0.180715, -0.398302], "-2.50657 0.0451745 0.126915", "0.313725_0.313725_0.313725_0.000000_0.000000"),
    ("RDS5160_v39_2.stl", [-0.420630, 0.180715, -0.398302], "-2.50657 0.0451745 0.126915", "0.964706_0.109804_0.407843_0.000000_0.000000"),
    ("RDS5160_v39.stl", [-0.420630, 0.180715, -0.398302], "-2.50657 0.0451745 0.126915", "0.313725_0.313725_0.313725_0.000000_0.000000"),
    ("RDS5160_v39_3.stl", [-0.396648, 0.203202, -0.385293], "3.0397 0.629318 -1.55467", "0.313725_0.313725_0.313725_0.000000_0.000000"),
    ("RDS3235_Gear_25R_0_00_v5.stl", [-0.426728, 0.172761, -0.388313], "1.64686 0.934389 1.75892", "0.952941_0.796078_0.486275_0.000000_0.000000"),
    ("Wheel_v5.stl", [-0.364299, 0.180727, -0.391158], "3.0855 0.634273 -1.47714", "0.960784_0.960784_0.964706_0.000000_0.000000"),
    ("_6mm_Bearing_v2.stl", [-0.365785, 0.180537, -0.391090], "-2.50657 0.0451745 0.126915", "0.627451_0.627451_0.627451_0.000000_0.000000"),
    ("Wheel_gear_v6.stl", [-0.421278, 0.173456, -0.388561], "0.0760591 0.934389 1.75892", "0.960784_0.960784_0.964706_0.000000_0.000000")
]

for mesh, xyz, rpy, mat in wrist_meshes:
    new_xyz = np.array(xyz) + offset_wrist
    print(f"<visual>")
    print(f'    <origin xyz="{new_xyz[0]:.6f} {new_xyz[1]:.6f} {new_xyz[2]:.6f}" rpy="{rpy}" />')
    print(f'    <geometry>')
    print(f'        <mesh filename="file://$(find vector_description)/meshes/{mesh}" scale="1 1 1" />')
    print(f'    </geometry>')
    print(f'    <material name="{mat}"><color rgba="{ " ".join(mat.split("_")[:3]) } 1" /></material>')
    print(f'</visual>')

print("\n--- Mesh conversions for left_ee_link ---")
ee_meshes = [
    ("L_Hand_EE.stl", [-0.229956, 0.238738, -0.428489], "-0.0743689 0.91752 -1.50298", "0.917647_0.917647_0.917647_0.000000_0.000000")
]
for mesh, xyz, rpy, mat in ee_meshes:
    new_xyz = np.array(xyz) + offset_ee
    print(f"<visual>")
    print(f'    <origin xyz="{new_xyz[0]:.6f} {new_xyz[1]:.6f} {new_xyz[2]:.6f}" rpy="{rpy}" />')
    print(f'    <geometry>')
    print(f'        <mesh filename="file://$(find vector_description)/meshes/{mesh}" scale="1 1 1" />')
    print(f'    </geometry>')
    print(f'    <material name="{mat}"><color rgba="{ " ".join(mat.split("_")[:3]) } 1" /></material>')
    print(f'</visual>')
