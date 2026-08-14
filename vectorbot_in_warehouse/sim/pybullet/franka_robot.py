import pybullet as p
import pybullet_data
import time

p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())

# Load the ground plane
p.loadURDF("plane.urdf")
# Load the robot
panda_id = p.loadURDF("franka_panda/panda.urdf", basePosition=[0, 0, 0], useFixedBase=True)

# Set gravity
p.setGravity(0, 0, -9.81)

# Simulate loop
while True:
    p.stepSimulation()
    time.sleep(1. / 240.)
