#!/usr/bin/env python3

import pybullet as p
import pybullet_data
import time
import os
from ament_index_python.packages import get_package_share_directory

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory

import math

# Joint name mapping: control box → URDF
JOINT_NAME_MAP = {
    # Left arm
    "left_shoulder_1": "left_shoulder_holder",
    "left_shoulder_2": "left_shoulder",
    "left_elbow_1": "left_bicep",
    "left_elbow_2": "left_forearm",
    "left_wrist_1": "left_hand_palm",
    "left_wrist_2": "left_hand_finger",
    # Right arm
    "right_shoulder_1": "right_shoulder_holder",
    "right_shoulder_2": "right_shoulder",
    "right_elbow_1": "right_bicep",
    "right_elbow_2": "right_forearn",
    "right_wrist_1": "right_hand_palm",
    "right_wrist_2": "right_hand_finger",
    # Neck & head
    "neck_horizontal": "head",
    "neck_vertical": "neck",
}

def deg_to_rad(deg):
    return deg * math.pi / 180.0

class PyBulletSim(Node):
    def __init__(self):
        super().__init__('pybullet_sim_node')
        self.get_logger().info('Starting PyBullet simulation...')

        # Debug publisher
        self.joint_cmd_echo_pub = self.create_publisher(JointTrajectory, '/pybullet/joints/cmd', 10)

        # Subscriber
        self.subscription = self.create_subscription(
            JointTrajectory,
            '/joints/cmd',
            self.joint_command_callback,
            10
        )
        self.get_logger().info('Subscribed to /joints/cmd')

        # Initialize simulation
        self.init_simulation()

    def init_simulation(self):
        p.connect(p.GUI)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.loadURDF("plane.urdf")

        vector_description_path = get_package_share_directory('vector_description')
        urdf_path = os.path.join(vector_description_path, 'urdf', 'vector.urdf')

        self.robot_id = p.loadURDF(urdf_path, basePosition=[0, 0, 0], useFixedBase=False)
        p.setGravity(0, 0, -9.81)

        self.joint_name_to_id = {}
        num_joints = p.getNumJoints(self.robot_id)
        for i in range(num_joints):
            name = p.getJointInfo(self.robot_id, i)[1].decode('utf-8')
            self.joint_name_to_id[name] = i

        self.get_logger().info(f"Robot has {num_joints} joints.")
        self.get_logger().info(f"Available joints: {list(self.joint_name_to_id.keys())}")

    def joint_command_callback(self, msg: JointTrajectory):
        if not msg.points:
            self.get_logger().warn("Received JointTrajectory with no points.")
            return

        self.get_logger().info(f"Received JointTrajectory for joints: {msg.joint_names}")
        self.get_logger().info(f"Target positions: {msg.points[0].positions}")

        # Echo the command for monitoring
        self.joint_cmd_echo_pub.publish(msg)

        for name, position_deg in zip(msg.joint_names, msg.points[0].positions):
            if name not in JOINT_NAME_MAP:
                self.get_logger().warn(f"Joint '{name}' not in joint name mapping.")
                continue

            sim_name = JOINT_NAME_MAP[name]
            joint_id = self.joint_name_to_id.get(sim_name)
            if joint_id is None:
                self.get_logger().warn(f"Mapped joint '{sim_name}' not found in URDF.")
                continue

            # Convert to radians (URDF expects radians)
            position_rad = deg_to_rad(position_deg)

            p.setJointMotorControl2(
                bodyIndex=self.robot_id,
                jointIndex=joint_id,
                controlMode=p.POSITION_CONTROL,
                targetPosition=position_rad,
                force=5.0
            )

    def run(self):
        try:
            while rclpy.ok():
                rclpy.spin_once(self, timeout_sec=0)
                p.stepSimulation()
                time.sleep(1.0 / 240.0)
        except KeyboardInterrupt:
            p.disconnect()
            self.get_logger().info("Simulation stopped.")

def main(args=None):
    rclpy.init(args=args)
    sim_node = PyBulletSim()
    sim_node.run()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
