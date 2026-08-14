#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math

class MovementVerifier(Node):
    def __init__(self):
        super().__init__('movement_verifier')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(Odometry, '/base_controller/odom', self.odom_callback, 10)
        
        self.cmd_timer = self.create_timer(0.1, self.publish_cmd)
        self.start_sim_time = None
        self.latest_odom = None
        self.max_pitch = 0.0
        self.max_roll = 0.0

    def odom_callback(self, msg):
        self.latest_odom = msg
        # Extract orientation quaternion
        q = msg.pose.pose.orientation
        # Compute roll, pitch, yaw
        sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
        cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2 * (q.w * q.y - q.z * q.x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        self.max_roll = max(self.max_roll, abs(roll))
        self.max_pitch = max(self.max_pitch, abs(pitch))

        pos = msg.pose.pose.position
        print(f"Odom: Pos=[{pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f}] | RPY=[{math.degrees(roll):.1f}, {math.degrees(pitch):.1f}, {math.degrees(yaw):.1f}] deg", flush=True)

    def publish_cmd(self):
        current_time = self.get_clock().now()
        if self.start_sim_time is None:
            # Wait until simulation time starts moving
            if current_time.nanoseconds > 0:
                self.start_sim_time = current_time
            return
            
        elapsed = (current_time - self.start_sim_time).nanoseconds / 1e9
        msg = Twist()
        if elapsed < 4.0:
            msg.linear.x = 0.2
        else:
            msg.linear.x = 0.0
            
        self.pub.publish(msg)
        
        if elapsed > 5.0:
            self.get_logger().info("Verification complete.")
            print("\n--- RESULTS ---")
            if self.latest_odom:
                pos = self.latest_odom.pose.pose.position
                print(f"Final Position: X={pos.x:.3f}, Y={pos.y:.3f}")
                print(f"Max Roll Angle: {math.degrees(self.max_roll):.2f} deg")
                print(f"Max Pitch Angle: {math.degrees(self.max_pitch):.2f} deg")
                
                # Check if the robot drove forward and stayed upright
                if pos.x > 0.5 and self.max_pitch < 10.0 and self.max_roll < 10.0:
                    print("\nSTATUS: SUCCESS! The robot is stable and drives forward successfully.")
                else:
                    print("\nSTATUS: FAILED! Stability check did not pass.")
            else:
                print("No odometry messages received.")
            
            rclpy.shutdown()

def main():
    rclpy.init()
    node = MovementVerifier()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass

if __name__ == '__main__':
    main()
