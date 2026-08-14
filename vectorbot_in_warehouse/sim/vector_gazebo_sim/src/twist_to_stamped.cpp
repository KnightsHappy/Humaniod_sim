// twist_to_stamped.cpp
//
// Minimal C++ node that wraps geometry_msgs/Twist into geometry_msgs/TwistStamped.
//
// Why this exists: ROS 2 Jazzy's diff_drive_controller subscribes to
// /<controller_name>/cmd_vel and ONLY accepts TwistStamped. The Vector OS
// pipeline publishes plain Twist on /cmd_vel_final after twist_mux and
// velocity_limiter. This node bridges the two without any modifications
// to the OS code.
//
// Default topics (overridable via parameters):
//   input_topic   = /cmd_vel_final          (Twist)
//   output_topic  = /base_controller/cmd_vel (TwistStamped)
//
// Header stamp uses the node's clock — when use_sim_time:=true is set,
// this is /clock from Gazebo, which keeps the diff_drive_controller's
// staleness check happy.

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>

class TwistToStamped : public rclcpp::Node
{
public:
  TwistToStamped() : Node("twist_to_stamped")
  {
    const auto input_topic  = this->declare_parameter<std::string>("input_topic",  "/cmd_vel_final");
    const auto output_topic = this->declare_parameter<std::string>("output_topic", "/base_controller/cmd_vel");
    frame_id_ = this->declare_parameter<std::string>("frame_id", "base_link");

    pub_ = this->create_publisher<geometry_msgs::msg::TwistStamped>(output_topic, 10);
    sub_ = this->create_subscription<geometry_msgs::msg::Twist>(
      input_topic, 10,
      [this](const geometry_msgs::msg::Twist::SharedPtr msg) { this->callback(msg); });

    RCLCPP_INFO(this->get_logger(),
      "Bridging Twist '%s' → TwistStamped '%s' (frame_id='%s')",
      input_topic.c_str(), output_topic.c_str(), frame_id_.c_str());
  }

private:
  void callback(const geometry_msgs::msg::Twist::SharedPtr msg)
  {
    geometry_msgs::msg::TwistStamped out;
    out.header.stamp = this->get_clock()->now();
    out.header.frame_id = frame_id_;
    out.twist = *msg;
    pub_->publish(out);
  }

  std::string frame_id_;
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr sub_;
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr pub_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TwistToStamped>());
  rclcpp::shutdown();
  return 0;
}
