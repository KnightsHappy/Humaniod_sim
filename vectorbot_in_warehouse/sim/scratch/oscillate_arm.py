#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import time

class ArmOscillator(Node):
    def __init__(self):
        super().__init__('arm_oscillator')
        self.pub = self.create_publisher(JointTrajectory, '/joint_trajectory_controller/joint_trajectory', 10)
        self.timer = self.create_timer(2.0, self.timer_callback)
        self.state = 0
        self.get_logger().info("Arm oscillator started")

    def timer_callback(self):
        traj_msg = JointTrajectory()
        traj_msg.joint_names = ['left_bicep', 'left_forearm']
        
        point = JointTrajectoryPoint()
        if self.state == 0:
            point.positions = [1.0, 1.0]
            self.state = 1
        else:
            point.positions = [-1.0, -1.0]
            self.state = 0
            
        point.time_from_start = Duration(sec=1, nanosec=800000000) # 1.8s
        traj_msg.points.append(point)
        self.pub.publish(traj_msg)
        self.get_logger().info(f"Published positions: {point.positions}")

def main(args=None):
    rclpy.init(args=args)
    node = ArmOscillator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
