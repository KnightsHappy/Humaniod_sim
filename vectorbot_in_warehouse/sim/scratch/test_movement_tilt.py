import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math
import time
import subprocess
import json

class TiltMonitor(Node):
    def __init__(self):
        super().__init__('tilt_monitor')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.max_roll = 0.0
        self.max_pitch = 0.0
        self.max_tilt_mag = 0.0

    def query_gazebo_pose(self):
        # We can use the gz topic tool to get the pose of vector_robot directly
        try:
            res = subprocess.run(
                ["gz", "topic", "-e", "-t", "/world/vector_warehouse/pose/info", "-n", "1"],
                capture_output=True, text=True, timeout=1.0
            )
            output = res.stdout
            # Parse output to find vector_robot pose
            # We want to find the section matching name: "vector_robot"
            lines = output.split('\n')
            found_robot = False
            pose_lines = []
            for line in lines:
                if 'name: "vector_robot"' in line:
                    found_robot = True
                    pose_lines = []
                elif found_robot:
                    if 'name:' in line and 'vector_robot' not in line:
                        # Reached next model
                        break
                    pose_lines.append(line)
            
            if not found_robot:
                return None
                
            # Parse position and orientation from pose_lines
            # Format:
            #   position { x: ... y: ... z: ... }
            #   orientation { x: ... y: ... z: ... w: ... }
            x, y, z, w = 0.0, 0.0, 0.0, 1.0
            px, py, pz = 0.0, 0.0, 0.0
            
            in_pos = False
            in_ori = False
            for line in pose_lines:
                if 'position {' in line:
                    in_pos = True
                elif 'orientation {' in line:
                    in_ori = True
                elif '}' in line:
                    in_pos = False
                    in_ori = False
                elif in_pos:
                    if 'x:' in line: px = float(line.split(':')[1].strip())
                    if 'y:' in line: py = float(line.split(':')[1].strip())
                    if 'z:' in line: pz = float(line.split(':')[1].strip())
                elif in_ori:
                    if 'x:' in line: x = float(line.split(':')[1].strip())
                    if 'y:' in line: y = float(line.split(':')[1].strip())
                    if 'z:' in line: z = float(line.split(':')[1].strip())
                    if 'w:' in line: w = float(line.split(':')[1].strip())
            
            return (px, py, pz), (x, y, z, w)
        except Exception as e:
            # self.get_logger().error(f"Error querying pose: {e}")
            return None

    def quaternion_to_euler(self, q):
        x, y, z, w = q
        # roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        # yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return roll, pitch, yaw

def main():
    rclpy.init()
    node = TiltMonitor()
    
    print("Aligning and waiting for simulation...")
    time.sleep(2)
    
    pose_info = node.query_gazebo_pose()
    if pose_info is None:
        print("Could not get robot pose from Gazebo. Make sure simulation is running.")
        rclpy.shutdown()
        return
        
    (px, py, pz), (qx, qy, qz, qw) = pose_info
    r, p, y = node.quaternion_to_euler((qx, qy, qz, qw))
    print(f"Initial Pose: Pos=[{px:.3f}, {py:.3f}, {pz:.3f}], RPY=[{math.degrees(r):.2f}, {math.degrees(p):.2f}, {math.degrees(y):.2f}]")
    
    # We will send a forward command of 0.4 m/s for 1.5 seconds, then stop
    print("\nPublishing forward command...")
    msg = Twist()
    msg.linear.x = 0.4
    
    start_time = time.time()
    while time.time() - start_time < 2.0:
        node.cmd_pub.publish(msg)
        pose_info = node.query_gazebo_pose()
        if pose_info:
            _, (qx, qy, qz, qw) = pose_info
            r, p, y = node.quaternion_to_euler((qx, qy, qz, qw))
            tilt_mag = math.sqrt(r*r + p*p)
            if tilt_mag > node.max_tilt_mag:
                node.max_tilt_mag = tilt_mag
                node.max_roll = r
                node.max_pitch = p
        time.sleep(0.1)
        
    # Stop command
    print("Stopping...")
    msg.linear.x = 0.0
    start_time = time.time()
    while time.time() - start_time < 1.0:
        node.cmd_pub.publish(msg)
        pose_info = node.query_gazebo_pose()
        if pose_info:
            _, (qx, qy, qz, qw) = pose_info
            r, p, y = node.quaternion_to_euler((qx, qy, qz, qw))
            tilt_mag = math.sqrt(r*r + p*p)
            if tilt_mag > node.max_tilt_mag:
                node.max_tilt_mag = tilt_mag
                node.max_roll = r
                node.max_pitch = p
        time.sleep(0.1)
        
    print(f"\n--- MOVEMENT TILT RESULTS ---")
    print(f"Max Roll:  {math.degrees(node.max_roll):.2f} degrees")
    print(f"Max Pitch: {math.degrees(node.max_pitch):.2f} degrees")
    print(f"Max Tilt Magnitude: {math.degrees(node.max_tilt_mag):.2f} degrees")
    
    rclpy.shutdown()

if __name__ == '__main__':
    main()
