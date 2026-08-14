import pybullet as p
import pybullet_data
import os
import time

# Connect to the GUI
p.connect(p.GUI)

# Set search path to pybullet_data
p.setAdditionalSearchPath(pybullet_data.getDataPath())

# Load the ground plane
p.loadURDF("plane.urdf")

# Construct URDF path relative to this script
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # go from pybullet/ to src/
urdf_path = os.path.join(base_dir, 'vector_description', 'urdf', 'vector.urdf')

# Load your robot
robot_id = p.loadURDF(urdf_path, basePosition=[0, 0, 0], useFixedBase=False)

# Set gravity
p.setGravity(0, 0, -9.81)

# Simulate loop
while True:
    p.stepSimulation()
    time.sleep(1. / 240.)

