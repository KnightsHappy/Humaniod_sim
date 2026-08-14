import pybullet as p
import pybullet_data
import time
import os

# === Setup ===
p.connect(p.GUI)
p.setGravity(0, 0, -9.81)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.loadURDF("plane.urdf")

# === Local Paths ===
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # workspace root
vector_urdf_path = os.path.join(workspace_root, "vector_description", "urdf", "vector.urdf")
world1_urdf_path = os.path.join(workspace_root, "world1_description", "urdf", "world1.urdf")

warehouse_model_path = os.path.join(workspace_root, "aws-robomaker-small-warehouse-world", "models")
shelf_urdf_path = os.path.join(warehouse_model_path, "aws_robomaker_warehouse_ShelfF_01", "model.urdf")
pallet_urdf_path = os.path.join(warehouse_model_path, "aws_robomaker_warehouse_PalletJackB_01", "model.urdf")
trashcan_urdf_path = os.path.join(warehouse_model_path, "aws_robomaker_warehouse_TrashCanC_01", "model.urdf")
clutter_urdf_path = os.path.join(warehouse_model_path, "aws_robomaker_warehouse_ClutteringA_01", "model.urdf")

table_urdf_path = os.path.join(pybullet_data.getDataPath(), "table", "table.urdf")
cube_urdf_path = os.path.join(warehouse_model_path, "cube.urdf")


# === Load Models ===
# Load the humanoid robot
robot_id = p.loadURDF(vector_urdf_path, basePosition=[0, 0, 0.03], useFixedBase=False)

# Load world base
p.loadURDF(world1_urdf_path, basePosition=[0, 0, -0.05], useFixedBase=True)

# Load shelves
p.loadURDF(shelf_urdf_path, basePosition=[-8.5, 1, 0], useFixedBase=True)
p.loadURDF(shelf_urdf_path, basePosition=[8.5, -16, 0], useFixedBase=True)
p.loadURDF(shelf_urdf_path, basePosition=[1.2, -16, 0], useFixedBase=True)
p.loadURDF(shelf_urdf_path, basePosition=[7, 15, 0], useFixedBase=True)
p.loadURDF(shelf_urdf_path, basePosition=[17, 8, 0], useFixedBase=True)

# Load pallet jacks
p.loadURDF(pallet_urdf_path, basePosition=[-4, 7.5, 0], useFixedBase=True)
p.loadURDF(pallet_urdf_path, basePosition=[-3, 7.5, 0], useFixedBase=True)

# Load trash cans
p.loadURDF(trashcan_urdf_path, basePosition=[-1.5, 7.5, 0], useFixedBase=True)
p.loadURDF(trashcan_urdf_path, basePosition=[1.0, 8, 0], useFixedBase=True)
p.loadURDF(trashcan_urdf_path, basePosition=[1.0, 9, 0], useFixedBase=True)
p.loadURDF(trashcan_urdf_path, basePosition=[1.0, 10, 0], useFixedBase=True)

# Load cluttering items
p.loadURDF(clutter_urdf_path, basePosition=[-6, -7, 0], useFixedBase=True)
p.loadURDF(clutter_urdf_path, basePosition=[-3, -7, 0], useFixedBase=True)
p.loadURDF(clutter_urdf_path, basePosition=[-1, -7, 0], useFixedBase=True)
p.loadURDF(clutter_urdf_path, basePosition=[-6, 7.5, 0], useFixedBase=True)
p.loadURDF(clutter_urdf_path, basePosition=[-3, 3, 0], useFixedBase=True)
p.loadURDF(clutter_urdf_path, basePosition=[-5, 3, 0], useFixedBase=True)
p.loadURDF(clutter_urdf_path, basePosition=[-5, 1, 0], useFixedBase=True)


#robot and its objects
p.loadURDF(table_urdf_path, basePosition=[0, -3, 0], useFixedBase=True)
p.loadURDF(table_urdf_path, basePosition=[3, 0, 0], useFixedBase=True)
p.loadURDF(table_urdf_path, basePosition=[-2, -3, 0], useFixedBase=True)
p.loadURDF(table_urdf_path, basePosition=[2, -3, 0], useFixedBase=True)
p.loadURDF(cube_urdf_path, basePosition=[0, -2.8, 1], useFixedBase=False)

time.sleep(1)

# Get joint indices
joint_names = {}
for i in range(p.getNumJoints(robot_id)):
    name = p.getJointInfo(robot_id, i)[1].decode('utf-8')
    joint_names[name] = i
    print(f"{i}: {name}")

# Wheel joints
left_wheel = 15
right_wheel = 14

# Key mappings
wheel_velocity = 6.0
key_map = {
    ',': (-wheel_velocity, -wheel_velocity),     # forward
    'i': (wheel_velocity, wheel_velocity),   # backward
    'l': (wheel_velocity, -wheel_velocity),    # turn left
    'j': (-wheel_velocity, wheel_velocity),    # turn right
    'k': (0.0, 0.0)                             # stop
}

# Predefined poses
pose_left = {
    "left_shoulder": -0.2,
    "right_shoulder": 0.2,
}
pose_right = {
    "left_shoulder": 0.4,
    "right_shoulder": -0.4,
}
slider_joint = joint_names.get("slider_z_axis", None)

# Joint limit setup (assume known, adjust if needed)
slider_min = -0.4
slider_max = 0.4
slider_step = 0.002
slider_pos = 0.0  # starting value

# === Main Loop ===
while True:
    keys = p.getKeyboardEvents()

    left_vel = 0.0
    right_vel = 0.0
    move_slider_up = False
    move_slider_down = False

    for k in keys:
        if keys[k] & p.KEY_IS_DOWN:
            key_char = chr(k) if k < 256 else ''
            # wheel motion
            if key_char in key_map:
                print(f"Key '{key_char}' pressed")
                left_vel, right_vel = key_map[key_char]
            # pose triggers
            elif k == p.B3G_RIGHT_ARROW:
                for name, val in pose_right.items():
                    if name in joint_names:
                        p.setJointMotorControl2(robot_id, joint_names[name], p.POSITION_CONTROL, targetPosition=val, force=150)
            elif k == p.B3G_LEFT_ARROW:
                for name, val in pose_left.items():
                    if name in joint_names:
                        p.setJointMotorControl2(robot_id, joint_names[name], p.POSITION_CONTROL, targetPosition=val, force=150)
            elif k == p.B3G_UP_ARROW:
                move_slider_up = True
            elif k == p.B3G_DOWN_ARROW:
                move_slider_down = True

    # Apply wheel velocities
    p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=left_vel, force=10)
    p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=right_vel, force=10)

    # Update slider joint position
    if slider_joint is not None:
        if move_slider_up:
            slider_pos = min(slider_max, slider_pos + slider_step)
        elif move_slider_down:
            slider_pos = max(slider_min, slider_pos - slider_step)
        p.setJointMotorControl2(robot_id, slider_joint, p.POSITION_CONTROL, targetPosition=slider_pos, force=150)

    p.stepSimulation()
    time.sleep(1. / 240.)

