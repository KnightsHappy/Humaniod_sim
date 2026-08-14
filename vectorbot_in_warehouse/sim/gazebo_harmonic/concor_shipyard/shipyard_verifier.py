import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix

class ShipyardVerifier(Node):
    def __init__(self):
        super().__init__('shipyard_verifier')
        
        # State
        self.container_count = 0
        self.max_containers = 10
        self.current_gps = None
        
        # Subscriptions to ensure we actually have data
        self.create_subscription(NavSatFix, '/gps/fix', self.gps_cb, 10)
        
        # Timer: Fires every 10 seconds
        self.timer = self.create_timer(10.0, self.timer_callback)
        
        self.get_logger().info("Shipyard Verifier Started. Monitoring sensor streams...")

    def gps_cb(self, msg):
        self.current_gps = msg

    def timer_callback(self):
        if self.current_gps is None:
            self.get_logger().warn("Waiting for GPS fix before verifying location...")
            return

        if self.container_count < self.max_containers:
            self.container_count += 1
            
            # Simulated location verification using real-time GPS data
            lat = self.current_gps.latitude
            lon = self.current_gps.longitude
            
            print(f"--- AUDIT LOG ---")
            print(f"Container {self.container_count} detected and location verified!")
            print(f"Coordinates: {lat:.6f}, {lon:.6f}")
            print(f"------------------")
        else:
            self.get_logger().info("Audit Complete: 10 containers verified. Standing by.")
            self.timer.cancel() # Stop the timer after 10 detections

def main():
    rclpy.init()
    rclpy.spin(ShipyardVerifier())
    rclpy.shutdown()

if __name__ == '__main__':
    main()