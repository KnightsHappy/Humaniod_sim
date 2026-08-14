#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

class RightArmOscillator(Node):
    def __init__(self):
        super().__init__('right_arm_oscillator')
        self.pub = self.create_publisher(JointTrajectory, '/joint_trajectory_controller/joint_trajectory', 10)
        self.timer = self.create_timer(3.0, self.timer_callback)
        self.state = 0
        self.get_logger().info("Right arm oscillator started")

    def timer_callback(self):
        traj_msg = JointTrajectory()
        traj_msg.joint_names = [
            'right_shoulder_1', 'right_shoulder_2', 'right_bicep',
            'right_forearm', 'right_wrist_1', 'right_wrist_2'
        ]
        
        point = JointTrajectoryPoint()
        if self.state == 0:
            point.positions = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
            self.state = 1
        elif self.state == 1:
            point.positions = [-0.5, -0.5, -0.5, -0.5, -0.5, -0.5]
            self.state = 2
        else:
            point.positions = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            self.state = 0
            
        point.time_from_start = Duration(sec=2, nanosec=0)
        traj_msg.points.append(point)
        self.pub.publish(traj_msg)
        self.get_logger().info(f"Published positions: {point.positions}")

def main(args=None):
    rclpy.init(args=args)
    node = RightArmOscillator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
