// torso_teleop_bridge.cpp
//
// Bridges the Gazebo Teleop plugin's Q/E keys (linear.z in /cmd_vel)
// to torso position commands on /torso_position_controller/commands.
//
// The Gazebo Teleop plugin publishes geometry_msgs/Twist on /cmd_vel.
// - W/S → linear.x (handled by twist_to_stamped → diff_drive_controller)
// - A/D → angular.z (handled by twist_to_stamped → diff_drive_controller)
// - Q/E → linear.z  ← THIS NODE handles this axis
//
// When linear.z > 0 (Q key), the torso moves UP by incrementing the
// position setpoint. When linear.z < 0 (E key), the torso moves DOWN.
// The rate of movement is proportional to the linear.z value.
//
// Architecture:
//   /cmd_vel (Twist, from Gazebo Teleop plugin)
//     → torso_teleop_bridge (this node)
//     → /torso_position_controller/commands (Float64MultiArray)
//     → torso_safety_guard
//     → torso_position_pid
//     → torso_effort_controller
//     → slider_z_axis effort interface in Gazebo

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <algorithm>

class TorsoTeleopBridge : public rclcpp::Node
{
public:
  TorsoTeleopBridge() : Node("torso_teleop_bridge")
  {
    declare_parameter<double>("rate_m_per_s", 0.15);   // torso speed when key held
    declare_parameter<double>("min_position", 0.0);
    declare_parameter<double>("max_position", 0.39);
    declare_parameter<double>("update_hz", 20.0);

    rate_       = get_parameter("rate_m_per_s").as_double();
    min_pos_    = get_parameter("min_position").as_double();
    max_pos_    = get_parameter("max_position").as_double();
    double hz   = get_parameter("update_hz").as_double();

    // Start at max position (matches the startup auto-raise in torso_safety_guard)
    current_setpoint_ = max_pos_;

    torso_pub_ = create_publisher<std_msgs::msg::Float64MultiArray>(
      "/torso_position_controller/commands", 10);

    cmd_sub_ = create_subscription<geometry_msgs::msg::Twist>(
      "/cmd_vel", 10,
      [this](const geometry_msgs::msg::Twist::SharedPtr msg) {
        last_linear_z_ = msg->linear.z;
        last_cmd_time_ = now();
      });

    timer_ = create_wall_timer(
      std::chrono::milliseconds(static_cast<int>(1000.0 / hz)),
      [this]() { update(); });

    RCLCPP_INFO(get_logger(),
      "Torso teleop bridge active. Q=up, E=down at %.2f m/s. Range [%.2f, %.2f]",
      rate_, min_pos_, max_pos_);
  }

private:
  void update()
  {
    if ((now() - last_cmd_time_).seconds() > 0.2) {
      last_linear_z_ = 0.0;
    }

    if (std::abs(last_linear_z_) < 0.01) return;  // deadband

    double dt = 1.0 / 20.0;  // matches update_hz
    // Use sign only — move at fixed rate regardless of Teleop GUI slider value
    double direction = (last_linear_z_ > 0.0) ? 1.0 : -1.0;
    double delta = direction * rate_ * dt;
    current_setpoint_ = std::clamp(current_setpoint_ + delta, min_pos_, max_pos_);

    std_msgs::msg::Float64MultiArray msg;
    msg.data = {current_setpoint_};
    torso_pub_->publish(msg);

    RCLCPP_INFO_THROTTLE(get_logger(), *get_clock(), 500,
      "Torso teleop: setpoint=%.3f m (dir=%.0f)", current_setpoint_, direction);
  }

  double rate_{0.15};
  double min_pos_{0.0}, max_pos_{0.39};
  double current_setpoint_{0.39};
  double last_linear_z_{0.0};
  rclcpp::Time last_cmd_time_{0, 0, RCL_ROS_TIME};

  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_sub_;
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr torso_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TorsoTeleopBridge>());
  rclcpp::shutdown();
  return 0;
}
