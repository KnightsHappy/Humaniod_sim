import pybullet as p
import pybullet_data
import time
import os

# === Setup ===
p.connect(p.GUI)
p.setGravity(0, 0, -9.81)
p.setAdditionalSearchPath(pybullet_data.getDataPath())  # For plane.urdf etc.
p.loadURDF("plane.urdf")

# === local paths ===
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # workspace
vector_urdf_path = os.path.join(workspace_root, "vector_description", "urdf", "vector.urdf")
table_urdf_path = os.path.join(pybullet_data.getDataPath(), "table", "table.urdf")
cube_urdf_path = os.path.join(workspace_root, "aws-robomaker-small-warehouse-world", "models", "cube.urdf")

# === Load robot and objects ===
robot_id = p.loadURDF(vector_urdf_path, basePosition=[-0.5, 0, 0.03], useFixedBase=False)
p.loadURDF(table_urdf_path, basePosition=[1, 0, 0], useFixedBase=True)
p.loadURDF(cube_urdf_path, basePosition=[0.5, 0, 1], useFixedBase=False)
p.loadURDF(table_urdf_path, basePosition=[1, 4, 0], useFixedBase=True)

time.sleep(1)

# === Get joint indices ===
joint_names = {}
for i in range(p.getNumJoints(robot_id)):
    name = p.getJointInfo(robot_id, i)[1].decode('utf-8')
    joint_names[name] = i
    print(f"{i}: {name}")

# === Wheel joints and key mappings ===
left_wheel = 18
right_wheel = 17
wheel_velocity = 6.0
key_map = {
    ',': (-wheel_velocity, -wheel_velocity),     # backward
    'i': (wheel_velocity, wheel_velocity),   #  forward
    'l': (wheel_velocity, -wheel_velocity),    # turn left
    'j': (-wheel_velocity, wheel_velocity),    # turn right
    'k': (0.0, 0.0)                             # stop
}

# === Predefined poses ===
pose_left = {"left_shoulder": -0.2, "right_shoulder": 0.2}
pose_right = {"left_shoulder": 0.4, "right_shoulder": -0.4}
slider_joint = joint_names.get("slider_z_axis", None)

# === Slider joint limits ===
slider_min = -0.4
slider_max = 0.4
slider_step = 0.002
slider_pos = 0.0

frame_count = 0  # Put this before your loop

# === Main Control Loop ===
while True:
    keys = p.getKeyboardEvents()

    left_vel = 0.0
    right_vel = 0.0
    move_slider_up = False
    move_slider_down = False

    for k in keys:
        if keys[k] & p.KEY_IS_DOWN:
            key_char = chr(k) if k < 256 else ''
            if key_char in key_map:
                print(f"Key '{key_char}' pressed")
                left_vel, right_vel = key_map[key_char]
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

    # Apply wheel motion
    p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=left_vel, force=10)
    p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=right_vel, force=10)

    # Update slider joint
    if slider_joint is not None:
        if move_slider_up:
            slider_pos = min(slider_max, slider_pos + slider_step)
        elif move_slider_down:
            slider_pos = max(slider_min, slider_pos - slider_step)
        p.setJointMotorControl2(robot_id, slider_joint, p.POSITION_CONTROL, targetPosition=slider_pos, force=150)

    p.stepSimulation()


    frame_count += 1
    if frame_count % 10 == 0:  # Only every 10th frame (24 FPS → ~2.4 FPS)
        # === Camera view from joint 16 ===
        cam_link_state = p.getLinkState(robot_id, 16)
        cam_pos = cam_link_state[0]
        cam_orient = cam_link_state[1]

        cam_rot_matrix = p.getMatrixFromQuaternion(cam_orient)
        forward_vec = [cam_rot_matrix[0], cam_rot_matrix[3], cam_rot_matrix[6]]
        up_vec = [cam_rot_matrix[2], cam_rot_matrix[5], cam_rot_matrix[8]]
        cam_target = [cam_pos[0] + forward_vec[0], cam_pos[1] + forward_vec[1], cam_pos[2] + forward_vec[2]]

        view_matrix = p.computeViewMatrix(cam_pos, cam_target, up_vec)
        projection_matrix = p.computeProjectionMatrixFOV(fov=60, aspect=1.0, nearVal=0.1, farVal=100)

        img_arr = p.getCameraImage(
            width=160, height=120,  # Lower resolution
            viewMatrix=view_matrix,
            projectionMatrix=projection_matrix,
            renderer=p.ER_TINY_RENDERER  # Much faster than default OpenGL renderer
        )



    time.sleep(1. / 240.)

