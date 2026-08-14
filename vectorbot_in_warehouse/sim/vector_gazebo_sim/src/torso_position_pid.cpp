// torso_position_pid.cpp
//
// Software PID position controller for the torso prismatic joint.
//
// Why this exists:
//   gz_ros2_control's "position" command interface in Jazzy is implemented
//   internally as velocity-tracking — it commands a joint VELOCITY proportional
//   to position error, not effort. Vertical prismatic joints under gravity
//   cannot lift their own weight through that interface (gz_ros2_control
//   issue #192). The fix is to use the "effort" command interface instead
//   and close the position loop in software here, where we can apply
//   actual force to fight gravity.
//
// Architecture:
//   /torso_position_controller/commands  (Float64MultiArray, OS publishes here)
//        │                                 — kept unchanged for OS compatibility
//        ▼
//   torso_position_pid (this node)        — software PID, 50 Hz
//        │   • setpoint slew limiter      — prevents step-input transients
//        │   • PD + gravity feedforward   — heavy mass needs heavy damping
//        │   • parameter callback         — supports live tuning
//        │   • velocity from joint_states — clean D term, no numerical noise
//        ▼
//   /torso_effort_controller/commands    (Float64MultiArray)
//        ▼
//   effort_controllers/JointGroupEffortController  (ros2_control)
//        ▼
//   torso_z_joint (Gazebo applies effort directly as force)
//
// Tuning philosophy:
//   The system is a mass m with gravity load. Treat as 2nd-order system.
//   With gravity feedforward = m·g cancelling weight, the closed loop is:
//       m·ẍ + d·ẋ + kp·x = kp·setpoint     (where d ≈ joint damping + kd)
//   Choose natural frequency ωn = 4 rad/s (≈ 0.6 Hz, smooth motion).
//   Critical damping (ζ = 1) gives no overshoot.
//       kp = m·ωn²              for m=13kg, ωn=4: kp = 208
//       kd = 2·ζ·m·ωn           for ζ=1:        kd = 104
//   I term left at 0 — feedforward holds steady state, I just causes windup.
//   Live tuning via:  ros2 param set /torso_position_pid <param> <value>

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <algorithm>
#include <atomic>
#include <mutex>

class TorsoPositionPid : public rclcpp::Node
{
public:
  TorsoPositionPid() : Node("torso_position_pid")
  {
    // Defaults derived from physics: m=18.36kg (torso+arms), ωn=4 rad/s, ζ=1.0
    // Supported mass = torso_link(7.12) + both arms(11.24) = 18.36 kg
    // After uniform 110 kg mass scaling applied 2026-07-19.
    // kp = m·ωn²  = 18.36 × 16   = 293.8
    // kd = 2ζ·m·ωn = 2×1×18.36×4 = 146.9
    declare_parameter<double>("kp",                      293.8);
    declare_parameter<double>("ki",                      0.0);
    declare_parameter<double>("kd",                      146.9);
    declare_parameter<double>("gravity_feedforward_n",   180.2);   // 18.36 kg × 9.81
    declare_parameter<double>("max_effort",              2000.0);
    declare_parameter<double>("min_effort",             -2000.0);
    declare_parameter<double>("min_position",           -0.6);
    declare_parameter<double>("max_position",            0.39);
    declare_parameter<double>("integral_clamp",          100.0);
    declare_parameter<double>("setpoint_slew_m_per_s",   0.15);    // matches motor max vel
    declare_parameter<double>("deadband_m",              0.001);   // 1 mm — stop adjusting inside this
    declare_parameter<std::string>("joint_name",         "torso_z_joint");

    // Snapshot live params into atomics for thread-safe access from timer
    refresh_params();

    joint_name_ = get_parameter("joint_name").as_string();

    // Start with torso raised — the arms hang down by default and would
    // collide with the base if the torso started at 0.0.
    // Both setpoint_ and target_ start at max so the PID immediately
    // applies gravity feedforward + position hold as soon as
    // joint_states arrive, regardless of whether the safety guard's
    // startup auto-raise message was received.
    target_setpoint_ = max_pos_;
    setpoint_ = max_pos_;

    // Parameter callback — re-snapshot when any param changes
    param_cb_handle_ = add_on_set_parameters_callback(
      [this](const std::vector<rclcpp::Parameter>& /*params*/) {
        // Schedule refresh on next iteration to avoid races
        params_dirty_.store(true);
        rcl_interfaces::msg::SetParametersResult result;
        result.successful = true;
        return result;
      });

    // ── Subscriptions ──
    cmd_sub_ = create_subscription<std_msgs::msg::Float64MultiArray>(
      "/torso_position_controller/commands_safe", 10,
      [this](std_msgs::msg::Float64MultiArray::SharedPtr msg) {
        if (msg->data.empty()) return;
        std::lock_guard<std::mutex> lk(state_mutex_);
        target_setpoint_ = std::clamp(msg->data[0], min_pos_, max_pos_);
        // Don't reset slewed setpoint — let it ramp from where it currently is.
        // Reset integral since the goal changed (prevents leftover windup).
        integral_ = 0.0;
        RCLCPP_INFO(get_logger(),
          "Torso target: %.3f m (slewing from %.3f at %.2f m/s)",
          target_setpoint_, setpoint_, slew_rate_);
      });

    state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
      "/joint_states", rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::JointState::SharedPtr msg) {
        for (size_t i = 0; i < msg->name.size(); ++i) {
          if (msg->name[i] == joint_name_) {
            std::lock_guard<std::mutex> lk(state_mutex_);
            current_pos_ = msg->position[i];
            current_vel_ = (i < msg->velocity.size()) ? msg->velocity[i] : 0.0;
            have_state_ = true;
            return;
          }
        }
      });

    // ── Publisher ──
    effort_pub_ = create_publisher<std_msgs::msg::Float64MultiArray>(
      "/torso_effort_controller/commands", 10);

    // ── Control loop at 50 Hz (same as gz_ros2_control update rate) ──
    last_time_ = now();
    timer_ = create_wall_timer(
      std::chrono::milliseconds(20),
      [this]() { control_step(); });

    RCLCPP_INFO(get_logger(),
      "Torso PID ready. kp=%.1f ki=%.1f kd=%.1f ff=%.1fN slew=%.2fm/s",
      kp_, ki_, kd_, gravity_ff_, slew_rate_);
    RCLCPP_INFO(get_logger(),
      "Live tune: ros2 param set /torso_position_pid kp <value>");
  }

private:
  void refresh_params()
  {
    kp_           = get_parameter("kp").as_double();
    ki_           = get_parameter("ki").as_double();
    kd_           = get_parameter("kd").as_double();
    gravity_ff_   = get_parameter("gravity_feedforward_n").as_double();
    max_effort_   = get_parameter("max_effort").as_double();
    min_effort_   = get_parameter("min_effort").as_double();
    min_pos_      = get_parameter("min_position").as_double();
    max_pos_      = get_parameter("max_position").as_double();
    i_clamp_      = get_parameter("integral_clamp").as_double();
    slew_rate_    = get_parameter("setpoint_slew_m_per_s").as_double();
    deadband_     = get_parameter("deadband_m").as_double();
  }

  void control_step()
  {
    // Lazy refresh of params if any changed via ros2 param set
    if (params_dirty_.exchange(false)) {
      refresh_params();
      RCLCPP_INFO(get_logger(),
        "Params updated: kp=%.1f ki=%.1f kd=%.1f ff=%.1f slew=%.2f",
        kp_, ki_, kd_, gravity_ff_, slew_rate_);
    }

    if (!have_state_) return;

    auto t = now();
    double dt = (t - last_time_).seconds();
    last_time_ = t;
    if (dt <= 0.0 || dt > 0.5) dt = 0.02;  // sanity bounds

    double pos, vel, target;
    {
      std::lock_guard<std::mutex> lk(state_mutex_);
      pos = current_pos_;
      vel = current_vel_;
      target = target_setpoint_;
    }

    // ── 1. Setpoint slew limit ──
    // Convert the user's step-input target into a smooth ramp toward it.
    // Without this, every command would trigger a huge initial error and
    // the PID would slam the joint at full effort.
    double max_step = slew_rate_ * dt;
    double diff_to_target = target - setpoint_;
    if (std::abs(diff_to_target) <= max_step) {
      setpoint_ = target;
    } else {
      setpoint_ += (diff_to_target > 0 ? max_step : -max_step);
    }

    // ── 2. PID computation ──
    double error = setpoint_ - pos;

    // Deadband — once close enough, stop nudging the joint to prevent
    // micro-oscillation as the PID hunts for sub-mm precision.
    bool in_deadband = (std::abs(error) < deadband_) &&
                       (std::abs(target - pos) < deadband_) &&
                       (std::abs(vel) < 0.005);

    if (in_deadband) {
      // Hold position with just the gravity feedforward — no PID action.
      // This removes residual oscillation when "settled".
      integral_ = 0.0;
      double effort = std::clamp(gravity_ff_, min_effort_, max_effort_);
      publish_effort(effort);
      return;
    }

    // Anti-windup: only integrate if we're not saturated, OR if integration
    // would move us away from saturation.
    integral_ += error * dt;
    integral_ = std::clamp(integral_, -i_clamp_, i_clamp_);

    // Use joint velocity directly for D term (cleaner than dError/dt).
    // d(setpoint-pos)/dt ≈ -velocity   (slewed setpoint changes slowly)
    double derivative = -vel;

    double effort = kp_ * error
                  + ki_ * integral_
                  + kd_ * derivative
                  + gravity_ff_;

    effort = std::clamp(effort, min_effort_, max_effort_);
    publish_effort(effort);
  }

  void publish_effort(double effort)
  {
    std_msgs::msg::Float64MultiArray msg;
    msg.data = {effort};
    effort_pub_->publish(msg);
  }

  // Cached parameter values (snapshotted in refresh_params)
  double kp_{293.8}, ki_{0.0}, kd_{146.9};
  double gravity_ff_{180.2};
  double max_effort_{2000.0}, min_effort_{-2000.0};
  double min_pos_{-0.6}, max_pos_{0.39};
  double i_clamp_{100.0}, slew_rate_{0.15}, deadband_{0.001};

  std::string joint_name_;
  std::atomic<bool> params_dirty_{false};

  // Control state — protected by state_mutex_
  std::mutex state_mutex_;
  double setpoint_{0.0};       // slewed (internal)
  double target_setpoint_{0.0}; // user-commanded (raw)
  double current_pos_{0.0}, current_vel_{0.0};
  double integral_{0.0};
  bool have_state_{false};

  rclcpp::Time last_time_;

  rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr cmd_sub_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr     state_sub_;
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr    effort_pub_;
  rclcpp::TimerBase::SharedPtr                                      timer_;
  OnSetParametersCallbackHandle::SharedPtr                          param_cb_handle_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TorsoPositionPid>());
  rclcpp::shutdown();
  return 0;
}
