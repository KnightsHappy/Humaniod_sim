#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray, String
from sensor_msgs.msg import Image
import numpy as np
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import pybullet as p
import pybullet_data
import os
import time
from ament_index_python.packages import get_package_share_directory
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf_transformations
from tf2_ros import TransformBroadcaster
import asyncio
import websockets
import threading
import json

class UnifiedPyBulletController(Node):
    def __init__(self):
        super().__init__('unified_pybullet_controller')

        # Setup WebSocket server in a thread
        self.ws_port = 9001
        self.ws_thread = threading.Thread(target=self.start_websocket_server, daemon=True)
        self.ws_thread.start()

        # PyBullet GUI and setup
        p.connect(p.GUI)
        p.setGravity(0, 0, -9.81)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.loadURDF("plane.urdf")

        # Load robot and warehouse world
        self.vector_urdf_path = self.get_model_path('vector_description', 'urdf/vector.urdf')
        self.world1_urdf_path = self.get_model_path('world1_description', 'urdf/world1.urdf')
        script_dir = os.path.dirname(os.path.realpath(__file__))
        workspace_root = os.path.abspath(os.path.join(script_dir, '../../../'))
        warehouse_model_path = os.path.join(workspace_root, 'aws_robomaker_small_warehouse_world',
                                            'share', 'aws_robomaker_small_warehouse_world', 'models')

        self.shelf_path = self.check_path(os.path.join(warehouse_model_path, 'aws_robomaker_warehouse_ShelfF_01/model.urdf'))
        self.pallet_path = self.check_path(os.path.join(warehouse_model_path, 'aws_robomaker_warehouse_PalletJackB_01/model.urdf'))
        self.trashcan_path = self.check_path(os.path.join(warehouse_model_path, 'aws_robomaker_warehouse_TrashCanC_01/model.urdf'))
        self.clutter_path = self.check_path(os.path.join(warehouse_model_path, 'aws_robomaker_warehouse_ClutteringA_01/model.urdf'))
        self.cube_path = self.check_path(os.path.join(warehouse_model_path, 'cube.urdf'))
        self.table_path = os.path.join(pybullet_data.getDataPath(), 'table', 'table.urdf')

        self.load_models()

        # Load robot and list joints
        self.vector_id = p.loadURDF(self.vector_urdf_path, basePosition=[0, 0, 0.03], useFixedBase=False)
        self.print_all_joint_names()

        # Base control params
        self.wheel_radius = 0.05
        self.wheel_distance = 0.3
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0

        # Z-axis slider
        self.slider_joint_index = 0
        self.lower_limit = -0.6
        self.upper_limit = 0.3

        # ROS Subscriptions and Pubs
        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        self.create_subscription(Float32MultiArray, '/z_axis/cmd', self.z_axis_cmd_callback, 10)
        self.feedback_pub = self.create_publisher(String, '/z_axis/feedback', 10)
        self.camera_feed_pub = self.create_publisher(Image, '/oakd_camera_node/rgb/image_raw', 10)

        # Timer
        self.create_timer(0.1, self.publish_feedback)

        self.joint_name_to_index = {
            'left_shoulder_holder': 2,
            'left_shoulder': 3,
            'left_bicep': 4,
            'left_forearm': 5,
            'left_hand_palm': 6,
            'right_shoulder_holder': 8,
            'right_shoulder': 9,
            'right_bicep': 10,
            'right_forearn': 11,  # typo preserved
            'neck': 14,
            'head': 15
        }
        self.frame_count = 0

        self.sdk_to_sim_joint_names = {
            "neck_vertical": "neck",
            "neck_horizontal": "head",
            "left_shoulder_1": "left_shoulder_holder",
            "left_shoulder_2": "left_shoulder",
            "left_elbow_1": "left_bicep",
            "left_elbow_2": "left_forearm",
            "left_wrist_1": "left_hand_palm",
            "left_wrist_2": "left_hand_finger",
            "right_shoulder_1": "right_shoulder_holder",
            "right_shoulder_2": "right_shoulder",
            "right_elbow_1": "right_bicep",
            "right_elbow_2": "right_forearn",
            "right_wrist_1": "right_hand_palm",
            "right_wrist_2": "right_hand_finger",
        }

        self.joints_cmd_pub = self.create_publisher(JointTrajectory, '/joints/cmd', 10)
        self.create_subscription(JointTrajectory, '/joints/cmd', self.joints_cmd_callback, 10)
        self.joints_feedback_pub = self.create_publisher(JointTrajectory, '/joints/feedback', 10)

        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)


    def print_all_joint_names(self):
        print("=== [PyBullet] Listing all joint names in simulation ===")
        for i in range(p.getNumJoints(self.vector_id)):
            joint_info = p.getJointInfo(self.vector_id, i)
            print(f"[{i}] Joint Name: {joint_info[1].decode('utf-8')}")
        print("========================================================")
    
    def get_all_joint_names(self):
        return {p.getJointInfo(self.vector_id, i)[1].decode("utf-8") for i in range(p.getNumJoints(self.vector_id))}

    def suggest_closest_joint_name(self, name, candidates):
        import difflib
        matches = difflib.get_close_matches(name, candidates, n=1)
        return matches[0] if matches else None


    def joints_cmd_callback(self, msg: JointTrajectory):
        if not msg.points:
            self.get_logger().warn("Received joint command with no points.")
            return

        point = msg.points[0]
        positions = point.positions

        if len(msg.joint_names) != len(positions):
            self.get_logger().warn("Mismatch between joint names and positions count.")
            return

        for sdk_name, position in zip(msg.joint_names, positions):
            sim_name = self.sdk_to_sim_joint_names.get(sdk_name)
            if sim_name is None:
                valid_keys = list(self.sdk_to_sim_joint_names.keys())
                suggestion = self.suggest_closest_joint_name(sdk_name, valid_keys)
                self.get_logger().warn(f"Unknown SDK joint name: '{sdk_name}'. Valid keys: {valid_keys}")
                if suggestion:
                    self.get_logger().warn(f"Did you mean '{suggestion}'?")
                continue

            joint_index = self.joint_name_to_index.get(sim_name)
            if joint_index is None:
                valid_sim = list(self.joint_name_to_index.keys())
                suggestion = self.suggest_closest_joint_name(sim_name, valid_sim)
                self.get_logger().warn(f"Sim joint name '{sim_name}' not found in joint_name_to_index.")
                if suggestion:
                    self.get_logger().warn(f"Did you mean '{suggestion}'?")
                continue

            p.setJointMotorControl2(
                bodyIndex=self.vector_id,
                jointIndex=joint_index,
                controlMode=p.POSITION_CONTROL,
                targetPosition=position
            )

        self.joints_feedback_pub.publish(msg)


    def start_websocket_server(self):
        async def handler(websocket):
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if 'joint_trajectory_msg' in data:
                        jt = data['joint_trajectory_msg']
                        if 'joint_names' in jt and 'points' in jt and jt['points']:
                            point_data = jt['points'][0]  # assuming single point for now
                            if 'positions' in point_data:
                                msg = JointTrajectory()
                                msg.joint_names = jt['joint_names']
                                point = JointTrajectoryPoint()
                                point.positions = point_data['positions']
                                time_from_start = point_data.get('time_from_start', {'sec': 1, 'nanosec': 0})
                                point.time_from_start.sec = time_from_start.get('sec', 1)
                                point.time_from_start.nanosec = time_from_start.get('nanosec', 0)
                                msg.points.append(point)
                                self.joints_cmd_pub.publish(msg)  # ✅ Publish it so ROS callback gets triggered
                                print(f"[INFO] Published joint command: {msg}")
                except Exception as e:
                    print(f"WebSocket error: {e}")


        async def main():
            async with websockets.serve(handler, "0.0.0.0", self.ws_port):
                print(f"[INFO] WebSocket server running on port {self.ws_port}")
                await asyncio.Future()  # run forever

        asyncio.run(main())

    def handle_joint_trajectory(self, msg):
        valid_joint_names = get_all_joint_names()  # from PyBullet
        for name in msg.joint_names:
            if name not in valid_joint_names:
                print(f"[WARNING] Unknown joint name received in command: {name}")
                print(f"Available joints: {valid_joint_names}")
            else:
                print(f"[INFO] Command received for valid joint: {name}")


    def get_model_path(self, package_name, relative_path):
        pkg_share = get_package_share_directory(package_name)
        abs_path = os.path.join(pkg_share, relative_path)
        return self.check_path(abs_path)

    def check_path(self, path):
        if not os.path.exists(path):
            self.get_logger().error(f"URDF file not found: {path}")
            raise FileNotFoundError(path)
        return path

    def load_models(self):
        
        self.world1_id = p.loadURDF(self.world1_urdf_path, basePosition=[0, 0, -0.05], useFixedBase=True)
        self.left_wheel_joint = 18
        self.right_wheel_joint = 17

        for pos in [[-8.5, 1, 0], [8.5, -16, 0], [1.2, -16, 0], [7, 15, 0], [17, 8, 0]]:
            p.loadURDF(self.shelf_path, basePosition=pos, useFixedBase=True)

        for pos in [[-4, 7.5, 0], [-3, 7.5, 0]]:
            p.loadURDF(self.pallet_path, basePosition=pos, useFixedBase=True)

        for pos in [[-1.5, 7.5, 0], [1.0, 8, 0], [1.0, 9, 0], [1.0, 10, 0]]:
            p.loadURDF(self.trashcan_path, basePosition=pos, useFixedBase=True)

        for pos in [[-6, -7, 0], [-3, -7, 0], [-1, -7, 0], [-6, 7.5, 0], [-3, 3, 0], [-5, 3, 0], [-5, 1, 0]]:
            p.loadURDF(self.clutter_path, basePosition=pos, useFixedBase=True)

        for pos in [[0, -3, 0], [3, 0, 0], [-2, -3, 0], [2, -3, 0]]:
            p.loadURDF(self.table_path, basePosition=pos, useFixedBase=True)

        p.loadURDF(self.cube_path, basePosition=[0, -2.8, 1], useFixedBase=False)
        
        self.create_timer(1.0/10.0, self.publish_camera_feed)  # 30Hz
        self.get_logger().info("All models loaded successfully.")
        time.sleep(1)

    def cmd_vel_callback(self, msg):
        self.linear_velocity = msg.linear.x
        self.angular_velocity = msg.angular.z

    def z_axis_cmd_callback(self, msg):
        if len(msg.data) != 2:
            self.get_logger().warn("Expected 2 elements for /z_axis/cmd")
            return
        position = max(self.lower_limit, min(self.upper_limit, msg.data[0]))
        velocity = msg.data[1]
        p.setJointMotorControl2(self.vector_id, self.slider_joint_index, controlMode=p.POSITION_CONTROL, targetPosition=position, targetVelocity=velocity, force=100)
        self.get_logger().info(f"Z-axis -> Position: {position}, Velocity: {velocity}")

    def publish_camera_feed(self):
        # Get camera parameters and setup view
        cam_link_state = p.getLinkState(self.vector_id, 16)
        cam_pos = cam_link_state[0]
        cam_orient = cam_link_state[1]

        cam_rot_matrix = p.getMatrixFromQuaternion(cam_orient)
        forward_vec = [cam_rot_matrix[0], cam_rot_matrix[3], cam_rot_matrix[6]]
        up_vec = [cam_rot_matrix[2], cam_rot_matrix[5], cam_rot_matrix[8]]
        cam_target = [cam_pos[0] + forward_vec[0], cam_pos[1] + forward_vec[1], cam_pos[2] + forward_vec[2]]

        view_matrix = p.computeViewMatrix(cam_pos, cam_target, up_vec)
        projection_matrix = p.computeProjectionMatrixFOV(fov=60, aspect=1.0, nearVal=0.1, farVal=100)

        # Get camera image - returns tuple (width, height, rgbPixels, depthPixels, segmentationMaskBuffer)
        width, height, rgb_array, _, _ = p.getCameraImage(
            width=160, 
            height=120,
            viewMatrix=view_matrix,
            projectionMatrix=projection_matrix,
            renderer=p.ER_TINY_RENDERER
        )
        
        # Create and populate ROS Image message
        img_msg = Image()
        img_msg.header.stamp = self.get_clock().now().to_msg()
        img_msg.header.frame_id = "camera_link"  # Set your camera frame ID
        img_msg.height = height
        img_msg.width = width
        img_msg.encoding = "rgb8"
        img_msg.is_bigendian = False
        img_msg.step = width * 3  # 3 bytes per pixel (RGB)
        
        # Convert RGB array (which is actually RGBA) to RGB and flatten
        # PyBullet returns RGBA (4 channels) even when we ask for RGB
        rgb_data = np.array(rgb_array)[:, :, :3]  # Remove alpha channel
        img_msg.data = rgb_data.tobytes()
        
        self.camera_feed_pub.publish(img_msg)

    def publish_feedback(self):
        joint_state = p.getJointState(self.vector_id, self.slider_joint_index)
        msg = String()
        msg.data = f"Position: {joint_state[0]:.4f}, Velocity: {joint_state[1]:.4f}"
        self.feedback_pub.publish(msg)

        feedback = JointTrajectory()
        feedback.joint_names = list(self.joint_name_to_index.keys())
        point = JointTrajectoryPoint()
        for joint_name in feedback.joint_names:
            idx = self.joint_name_to_index[joint_name]
            js = p.getJointState(self.vector_id, idx)
            point.positions.append(js[0])
            point.velocities.append(js[1])
        point.time_from_start.sec = 0
        feedback.points.append(point)
        self.joints_feedback_pub.publish(feedback)

    def step_simulation(self):
        v = self.linear_velocity
        omega = self.angular_velocity
        L = self.wheel_distance
        R = self.wheel_radius

        left_speed = (v - (L / 2.0) * omega) / R
        right_speed = (v + (L / 2.0) * omega) / R

        p.setJointMotorControl2(self.vector_id, self.left_wheel_joint, p.VELOCITY_CONTROL, targetVelocity=left_speed, force=1.0)
        p.setJointMotorControl2(self.vector_id, self.right_wheel_joint, p.VELOCITY_CONTROL, targetVelocity=right_speed, force=1.0)

        p.stepSimulation()
        
        # self.publish_camera_feed()
        self.publish_odom()
        time.sleep(1.0 / 240.0)

    def publish_odom(self):
        pos, orn = p.getBasePositionAndOrientation(self.vector_id)
        linear_vel, angular_vel = p.getBaseVelocity(self.vector_id)
        quat = [orn[0], orn[1], orn[2], orn[3]]
        euler = tf_transformations.euler_from_quaternion(quat)
        now = self.get_clock().now().to_msg()

        odom_msg = Odometry()
        odom_msg.header.stamp = now
        odom_msg.header.frame_id = "odom"
        odom_msg.child_frame_id = "base_link"
        odom_msg.pose.pose.position.x = pos[0]
        odom_msg.pose.pose.position.y = pos[1]
        odom_msg.pose.pose.position.z = pos[2]
        odom_msg.pose.pose.orientation.x = quat[0]
        odom_msg.pose.pose.orientation.y = quat[1]
        odom_msg.pose.pose.orientation.z = quat[2]
        odom_msg.pose.pose.orientation.w = quat[3]
        odom_msg.twist.twist.linear.x = linear_vel[0]
        odom_msg.twist.twist.linear.y = linear_vel[1]
        odom_msg.twist.twist.linear.z = linear_vel[2]
        odom_msg.twist.twist.angular.x = angular_vel[0]
        odom_msg.twist.twist.angular.y = angular_vel[1]
        odom_msg.twist.twist.angular.z = angular_vel[2]

        self.odom_pub.publish(odom_msg)

        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = "odom"
        t.child_frame_id = "base_link"
        t.transform.translation.x = pos[0]
        t.transform.translation.y = pos[1]
        t.transform.translation.z = pos[2]
        t.transform.rotation.x = quat[0]
        t.transform.rotation.y = quat[1]
        t.transform.rotation.z = quat[2]
        t.transform.rotation.w = quat[3]
        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = UnifiedPyBulletController()

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0)
            node.step_simulation()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        p.disconnect()

if __name__ == '__main__':
    main()
