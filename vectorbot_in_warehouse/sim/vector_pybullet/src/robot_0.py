#!/usr/bin/env python3

import pybullet as p
import pybullet_data
import time
import os
from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.node import Node

class PyBulletSim(Node):
    def __init__(self):
        super().__init__('pybullet_sim_node')
        self.get_logger().info('Starting PyBullet simulation...')
        self.run_simulation()

    def run_simulation(self):
        p.connect(p.GUI)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.loadURDF("plane.urdf")

        # Dynamically get vector_description package path
        vector_description_path = get_package_share_directory('vector_description')
        urdf_path = os.path.join(vector_description_path, 'urdf', 'vector.urdf')

        robot_id = p.loadURDF(urdf_path, basePosition=[0, 0, 0], useFixedBase=False)
        p.setGravity(0, 0, -9.81)

        try:
            while rclpy.ok():
                p.stepSimulation()
                time.sleep(1. / 240.)
        except KeyboardInterrupt:
            p.disconnect()
            self.get_logger().info('Simulation stopped.')

def main(args=None):
    rclpy.init(args=args)
    sim_node = PyBulletSim()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

