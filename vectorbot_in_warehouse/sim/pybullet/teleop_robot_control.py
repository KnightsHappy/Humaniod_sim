import pybullet as p
import pybullet_data
import time
import os

# Connect to GUI
p.connect(p.GUI)

# Set search path
p.setAdditionalSearchPath(pybullet_data.getDataPath())

# Load the plane and robot
p.loadURDF("plane.urdf")

# Construct URDF path relative to this script
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # go from pybullet/ to src/
urdf_path = os.path.join(base_dir, 'vector_description', 'urdf', 'vector.urdf')

robot_id = p.loadURDF(urdf_path, basePosition=[0, 0, 0.03], useFixedBase=False)

# Set gravity
p.setGravity(0, 0, -9.81)

# Wheel joints
left_wheel = 15
right_wheel = 14

# Velocity control parameters
wheel_velocity = 6.0

# Key mapping
key_map = {
    ',': (wheel_velocity, wheel_velocity),     # forward
    'i': (-wheel_velocity, -wheel_velocity),   # backward
    'l': (-wheel_velocity, wheel_velocity),    # turn left
    'j': (wheel_velocity, -wheel_velocity),    # turn right
    'k': (0.0, 0.0)                             # stop
}

# Run simulation loop
while True:
    keys = p.getKeyboardEvents()

    left_vel = 0.0
    right_vel = 0.0

    for k in keys:
        key_char = chr(k) if k < 256 else ''
        if key_char in key_map and keys[k] & p.KEY_IS_DOWN:
            print(f"Key '{key_char}' pressed")  # Optional debug
            left_vel, right_vel = key_map[key_char]

    # Apply velocity control to the wheel joints
    p.setJointMotorControl2(robot_id, left_wheel, p.VELOCITY_CONTROL, targetVelocity=left_vel, force=10)
    p.setJointMotorControl2(robot_id, right_wheel, p.VELOCITY_CONTROL, targetVelocity=right_vel, force=10)

    p.stepSimulation()
    time.sleep(1. / 240.)

