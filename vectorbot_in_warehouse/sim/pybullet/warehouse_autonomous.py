import pybullet as p
import pybullet_data
import time
import math
import os

# === Setup ===
p.connect(p.GUI)
p.setGravity(0, 0, -9.81)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.loadURDF("plane.urdf")

# === Local Paths ===
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 2 levels up = workspace root

# Local URDFs
vector_urdf_path = os.path.join(workspace_root, "vector_description", "urdf", "vector.urdf")
world1_urdf_path = os.path.join(workspace_root, "world1_description", "urdf", "world1.urdf")

# Warehouse models
warehouse_model_path = os.path.join(workspace_root, "aws-robomaker-small-warehouse-world", "models")
shelf_urdf_path = os.path.join(warehouse_model_path, "aws_robomaker_warehouse_ShelfF_01", "model.urdf")
pallet_urdf_path = os.path.join(warehouse_model_path, "aws_robomaker_warehouse_PalletJackB_01", "model.urdf")
trashcan_urdf_path = os.path.join(warehouse_model_path, "aws_robomaker_warehouse_TrashCanC_01", "model.urdf")
clutter_urdf_path = os.path.join(warehouse_model_path, "aws_robomaker_warehouse_ClutteringA_01", "model.urdf")

# PyBullet data
table_urdf_path = os.path.join(pybullet_data.getDataPath(), "table", "table.urdf")
cube_urdf_path = os.path.join(pybullet_data.getDataPath(), "cube.urdf")

# === Load Models ===

# Load the humanoid robot
robot_id = p.loadURDF(vector_urdf_path, basePosition=[0, 0, 0.03], useFixedBase=False)

# Load world base
p.loadURDF(world1_urdf_path, basePosition=[0, 0, -0.05], useFixedBase=True)

# Load shelves
for pos in [[-8.5, 1, 0], [8.5, -16, 0], [1.2, -16, 0], [7, 15, 0], [17, 8, 0]]:
    p.loadURDF(shelf_urdf_path, basePosition=pos, useFixedBase=True)

# Load pallet jacks
for pos in [[-4, 7.5, 0], [-3, 7.5, 0]]:
    p.loadURDF(pallet_urdf_path, basePosition=pos, useFixedBase=True)

# Load trash cans
for pos in [[-1.5, 7.5, 0], [1.0, 8, 0], [1.0, 9, 0], [1.0, 10, 0]]:
    p.loadURDF(trashcan_urdf_path, basePosition=pos, useFixedBase=True)

# Load cluttering items
for pos in [[-6, -7, 0], [-3, -7, 0], [-1, -7, 0], [-6, 7.5, 0], [-3, 3, 0], [-5, 3, 0], [-5, 1, 0]]:
    p.loadURDF(clutter_urdf_path, basePosition=pos, useFixedBase=True)

# Load tables and cube
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
    ',': (wheel_velocity, wheel_velocity),     # Backwards
    'i': (-wheel_velocity, -wheel_velocity),   # Forward
    'l': (-wheel_velocity, wheel_velocity),    # Turn right
    'j': (wheel_velocity, -wheel_velocity),    # Turn left
    'k': (0.0, 0.0)                            # Stop
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

slider_min = -0.4
slider_max = 0.4
slider_step = 0.002
slider_pos = 0.0

def set_wheel_velocities(lv, rv, duration):
    t_end = time.time() + duration
    while time.time() < t_end:
        p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=lv, force=10)
        p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=rv, force=10)
        p.stepSimulation()
        time.sleep(1. / 240.)
    # Stop afterwards
    p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=0.0, force=10)
    p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=0.0, force=10)

def set_arm_pose(pose, duration):
    # Apply arm pose for the given duration
    for name, val in pose.items():
        if name in joint_names:
            p.setJointMotorControl2(robot_id, joint_names[name], p.POSITION_CONTROL, targetPosition=val, force=100)
    # Wait for the specified duration while maintaining the pose
    time.sleep(duration)

def set_arm_pose_firm(pose, duration):
    # Apply arm pose for the given duration
    for name, val in pose.items():
        if name in joint_names:
            p.setJointMotorControl2(robot_id, joint_names[name], p.POSITION_CONTROL, targetPosition=val, force=90)
    # Wait for the specified duration while maintaining the pose
    time.sleep(duration)

def move_slider_to(position, duration):
    global slider_pos
    slider_pos = max(slider_min, min(slider_max, position))  # clamp within limits
    p.setJointMotorControl2(robot_id, slider_joint, p.POSITION_CONTROL, targetPosition=slider_pos, force=50)
    t_end = time.time() + duration
    while time.time() < t_end:
        p.stepSimulation()
        time.sleep(1. / 240.)

def go_to_target_and_face_x(target_x=0.0, target_y=0.0):
    threshold = 0.05  # how close to the target is "close enough"
    max_duration = 10  # max seconds to try

    start_time = time.time()
    while time.time() - start_time < max_duration:
        pos, ori = p.getBasePositionAndOrientation(robot_id)
        x, y = pos[0], pos[1]

        dx = target_x - x
        dy = target_y - y
        distance = (dx**2 + dy**2)**0.5
        angle_to_target = math.atan2(dy, dx)

        if distance < threshold:
            break  # Close enough

        yaw = p.getEulerFromQuaternion(ori)[2]
        angle_diff = angle_to_target - yaw
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

        if abs(angle_diff) > 0.2:
            left = wheel_velocity if angle_diff > 0 else -wheel_velocity
            right = -left
        else:
            left = -wheel_velocity * 0.5
            right = -wheel_velocity * 0.5

        p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=left, force=10)
        p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=right, force=10)

        p.stepSimulation()
        time.sleep(1. / 240.)

    # Stop
    p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=0, force=10)
    p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=0, force=10)
    time.sleep(1)

    # Align to +X direction (you can customize this too)
    target_yaw = 0.0
    ori_align_start = time.time()
    while time.time() - ori_align_start < 5:
        _, ori = p.getBasePositionAndOrientation(robot_id)
        yaw = p.getEulerFromQuaternion(ori)[2]
        angle_diff = target_yaw - yaw
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

        if abs(angle_diff) < 0.05:
            break

        left = wheel_velocity * 0.5 if angle_diff > 0 else -wheel_velocity * 0.5
        right = -left

        p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=left, force=10)
        p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=right, force=10)

        p.stepSimulation()
        time.sleep(1. / 240.)
        
def go_to_target_and_face_y(target_x=0.0, target_y=0.0):
    threshold = 0.05  # how close to the target is "close enough"
    max_duration = 10  # max seconds to try

    start_time = time.time()
    while time.time() - start_time < max_duration:
        pos, ori = p.getBasePositionAndOrientation(robot_id)
        x, y = pos[0], pos[1]

        dx = target_x - x
        dy = target_y - y
        distance = (dx**2 + dy**2)**0.5
        angle_to_target = math.atan2(dy, dx)

        if distance < threshold:
            break  # Close enough

        yaw = p.getEulerFromQuaternion(ori)[2]
        angle_diff = angle_to_target - yaw
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

        if abs(angle_diff) > 0.2:
            left = wheel_velocity if angle_diff > 0 else -wheel_velocity
            right = -left
        else:
            left = -wheel_velocity * 0.5
            right = -wheel_velocity * 0.5

        p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=left, force=10)
        p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=right, force=10)

        p.stepSimulation()
        time.sleep(1. / 240.)

    # Stop
    p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=0, force=10)
    p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=0, force=10)
    time.sleep(1)

    # Align to +X direction (you can customize this too)
    target_yaw = -math.pi / 2
    ori_align_start = time.time()
    while time.time() - ori_align_start < 5:
        _, ori = p.getBasePositionAndOrientation(robot_id)
        yaw = p.getEulerFromQuaternion(ori)[2]
        angle_diff = target_yaw - yaw
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

        if abs(angle_diff) < 0.05:
            break

        left = wheel_velocity * 0.5 if angle_diff > 0 else -wheel_velocity * 0.5
        right = -left

        p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=left, force=10)
        p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=right, force=10)

        p.stepSimulation()
        time.sleep(1. / 240.)

    # Final stop
    p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=0, force=10)
    p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=0, force=10)
    time.sleep(1)


# === Startup Movement ===
# Open arms for seconds
# Stop wheels for seconds
set_wheel_velocities(0.0, 0.0, 1.0)
set_arm_pose(pose_right, 2.0)
# Stop wheels for seconds
set_wheel_velocities(0.0, 0.0, 1.0)
go_to_target_and_face_x(2.0, 0.0)
set_arm_pose(pose_left, 2.0)
# Stop wheels for seconds
set_wheel_velocities(0.0, 0.0, 2.0)
# Move slider up to 0.3 and hold for 2 seconds
move_slider_to(-0.1, 1.0)
move_slider_to(0.1, 1.0)
# Move back for seconds
set_wheel_velocities(wheel_velocity, wheel_velocity, 1.0)
# Stop wheels for seconds
set_wheel_velocities(0.0, 0.0, 1.0)
set_arm_pose_firm(pose_left, 1.0)
go_to_target_and_face_y(1.5, -2.0)
move_slider_to(0.5, 3.0)
set_wheel_velocities(-wheel_velocity, -wheel_velocity, 1.5)


#=== Movement 1 ===

# Open arms for seconds
set_arm_pose(pose_right, 2.0)
# Stop wheels for seconds
set_wheel_velocities(0.0, 0.0, 1.0)
set_wheel_velocities(wheel_velocity, wheel_velocity, 1.5)



#=== Movement 5 ===
# Move slider up to 0.3 and hold for 2 seconds
move_slider_to(0.0, 1.0)
go_to_target_and_face_x(0.0, -2.0)

def go_to_origin_and_face_x():
    threshold = 0.05  # how close to 0,0 is "close enough"
    max_duration = 10  # max seconds to try

    start_time = time.time()
    while time.time() - start_time < max_duration:
        pos, ori = p.getBasePositionAndOrientation(robot_id)
        x, y = pos[0], pos[1]

        distance = (x**2 + y**2)**0.5
        angle_to_origin = math.atan2(-y, -x)

        if distance < threshold:
            break  # Close enough

        # Rotation and movement logic
        yaw = p.getEulerFromQuaternion(ori)[2]
        angle_diff = angle_to_origin - yaw
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

        if abs(angle_diff) > 0.2:
            # Turn toward origin
            left = wheel_velocity if angle_diff > 0 else -wheel_velocity
            right = -left
        else:
            # Move forward slowly
            left = -wheel_velocity * 0.5
            right = -wheel_velocity * 0.5

        p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=left, force=10)
        p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=right, force=10)

        p.stepSimulation()
        time.sleep(1. / 240.)

    # Stop after reaching origin
    p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=0, force=10)
    p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=0, force=10)
    time.sleep(1)

    # === Face +X direction ===
    target_yaw = 0.0
    ori_align_start = time.time()
    while time.time() - ori_align_start < 5:  # up to 5 seconds to align
        _, ori = p.getBasePositionAndOrientation(robot_id)
        yaw = p.getEulerFromQuaternion(ori)[2]
        angle_diff = target_yaw - yaw
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

        if abs(angle_diff) < 0.05:
            break  # Close enough to +X

        left = wheel_velocity * 0.5 if angle_diff > 0 else -wheel_velocity * 0.5
        right = -left

        p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=left, force=10)
        p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=right, force=10)

        p.stepSimulation()
        time.sleep(1. / 240.)

    # Final stop
    p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=0, force=10)
    p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=0, force=10)
    time.sleep(1)

go_to_origin_and_face_x()


def perform_full_sequence():
    # === Startup Movement ===
    #=== Movement 1 ===
    set_arm_pose(pose_right, 2.0)
    set_wheel_velocities(0.0, 0.0, 1.0)
    set_wheel_velocities(-wheel_velocity, -wheel_velocity, 4.0)
    set_wheel_velocities(0.0, 0.0, 1.0)
    set_arm_pose(pose_left, 1.5)
    set_wheel_velocities(0.0, 0.0, 2.0)

    #=== Movement 2 ===
    set_wheel_velocities(wheel_velocity, wheel_velocity, 2.0)
    set_wheel_velocities(0.0, 0.0, 2.0)
    set_wheel_velocities(-wheel_velocity, wheel_velocity, 0.8)
    set_wheel_velocities(0.0, 0.0, 1.0)
    set_wheel_velocities(-wheel_velocity, -wheel_velocity, 3.0)
    set_wheel_velocities(0.0, 0.0, 3.0)

    #=== Movement 3 ===
    set_wheel_velocities(wheel_velocity, -wheel_velocity, 0.7)
    set_wheel_velocities(-wheel_velocity, -wheel_velocity, 1.5)
    set_wheel_velocities(0.0, 0.0, 2.0)
    set_wheel_velocities(-wheel_velocity, wheel_velocity, 0.7)
    set_wheel_velocities(-wheel_velocity, -wheel_velocity, 1.0)
    set_wheel_velocities(0.0, 0.0, 2.0)

    #=== Movement 4 ===
    set_wheel_velocities(wheel_velocity, wheel_velocity, 2.0)
    set_wheel_velocities(0.0, 0.0, 2.0)
    set_wheel_velocities(-wheel_velocity, wheel_velocity, 0.65)
    set_wheel_velocities(-wheel_velocity, -wheel_velocity, 3.0)
    set_wheel_velocities(wheel_velocity, -wheel_velocity, 0.7)
    set_wheel_velocities(0.0, 0.0, 2.0)

    #=== Movement 5 ===
    move_slider_to(0.2, 2.0)
    move_slider_to(-0.3, 2.0)
    move_slider_to(0.0, 2.0)

    # Return to origin and face +X
    go_to_origin_and_face_x()
    
    perform_full_sequence()
    
perform_full_sequence()


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
            elif k == p.B3G_RETURN:  # Enter key
                print("Enter key pressed: Executing predefined movement")
                set_wheel_velocities(wheel_velocity, -wheel_velocity, 1.0)
                set_wheel_velocities(-wheel_velocity, -wheel_velocity, 2.0)

    # Apply manual wheel velocities
    p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=left_vel, force=10)
    p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=right_vel, force=10)

    # Slider control
    if slider_joint is not None:
        if move_slider_up:
            slider_pos = min(slider_max, slider_pos + slider_step)
        elif move_slider_down:
            slider_pos = max(slider_min, slider_pos - slider_step)
        p.setJointMotorControl2(robot_id, slider_joint, p.POSITION_CONTROL, targetPosition=slider_pos, force=150)

    p.stepSimulation()
    time.sleep(1. / 240.)
