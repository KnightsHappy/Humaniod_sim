import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math
import time
import subprocess

class TiltMonitor(Node):
    def __init__(self):
        super().__init__('tilt_monitor')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

    def query_gazebo_pose(self):
        try:
            res = subprocess.run(
                ["gz", "topic", "-e", "-t", "/world/vector_warehouse/pose/info", "-n", "1"],
                capture_output=True, text=True, timeout=1.0
            )
            output = res.stdout
            lines = output.split('\n')
            found_robot = False
            pose_lines = []
            for line in lines:
                if 'name: "vector_robot"' in line:
                    found_robot = True
                    pose_lines = []
                elif found_robot:
                    if 'name:' in line and 'vector_robot' not in line:
                        break
                    pose_lines.append(line)
            
            if not found_robot:
                return None
                
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
            return None

    def quaternion_to_euler(self, q):
        x, y, z, w = q
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return roll, pitch, yaw

def main():
    rclpy.init()
    node = TiltMonitor()
    
    print("Waiting for topics to connect...")
    time.sleep(2)
    
    # Check initial pose
    pose = node.query_gazebo_pose()
    if pose:
        (px, py, pz), q = pose
        r, p, y = node.quaternion_to_euler(q)
        print(f"Initial: Pos=[{px:.3f}, {py:.3f}, {pz:.3f}], RPY=[{math.degrees(r):.2f}, {math.degrees(p):.2f}, {math.degrees(y):.2f}]")
        
    msg = Twist()
    msg.linear.x = 0.5 # 0.5 m/s
    
    print("Sending velocity commands...")
    for i in range(30): # 3 seconds
        node.cmd_pub.publish(msg)
        pose = node.query_gazebo_pose()
        if pose:
            (px, py, pz), q = pose
            r, p, y = node.quaternion_to_euler(q)
            print(f"Step {i:2d}: Pos=[{px:.3f}, {py:.3f}, {pz:.3f}], RPY=[{math.degrees(r):.2f}, {math.degrees(p):.2f}, {math.degrees(y):.2f}]")
        time.sleep(0.1)
        
    # Stop
    print("Stopping...")
    msg.linear.x = 0.0
    for i in range(10):
        node.cmd_pub.publish(msg)
        pose = node.query_gazebo_pose()
        if pose:
            (px, py, pz), q = pose
            r, p, y = node.quaternion_to_euler(q)
            print(f"Stop {i:2d}: Pos=[{px:.3f}, {py:.3f}, {pz:.3f}], RPY=[{math.degrees(r):.2f}, {math.degrees(p):.2f}, {math.degrees(y):.2f}]")
        time.sleep(0.1)
        
    rclpy.shutdown()

if __name__ == '__main__':
    main()
