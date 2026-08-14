// torso_safety_guard.cpp
//
// Intercepts torso position commands and clamps them to safe values
// based on current arm pose, preventing arm-base collisions.
//
// Problem:
//   The torso (and arms attached to it) can descend to ~0.60m above
//   ground. But if the arms are hanging straight down at full length,
//   the wrists/end-effectors are below 0.60m and would collide with
//   (or pass through) the base when the torso descends.
//
// Solution:
//   Subscribe to BOTH /joint_states (to know arm pose) and a "raw"
//   torso command topic. Re-publish to the actual torso PID input
//   only after clamping the setpoint based on arm safety.
//
// Architecture:
//   OS publishes Float64MultiArray on /torso_position_controller/commands
//        ↓
//   torso_safety_guard (this node)
//      • reads /joint_states for arm angles
//      • computes safe minimum torso height from arm pose
//      • clamps incoming command to >= safe_min
//      • republishes to /torso_position_controller/commands_safe
//        ↓
//   torso_position_pid subscribes to /torso_position_controller/commands_safe
//        ↓
//   torso_effort_controller → torso_z_joint
//
// Safety logic:
//   The arm is "tucked safely" if EITHER shoulder is raised enough OR
//   the elbow is bent enough that the end effector is above the base top.
//
//   Each arm independently. The most-extended arm wins (safer interpretation).
//
//   If both arms are clear, allow full descent (down to 0.0 m).
//   If either arm is in danger zone, clamp torso to a safe minimum
//   (currently 0.30 m on the joint, leaving the platform high enough
//   that arm tips clear the base by margin).
//
// Live-tunable parameters:
//   safe_min_torso_z:  joint position below which descent is forbidden
//                      when any arm is not safely positioned (default 0.30)
//   shoulder_safe_threshold_rad: shoulder_1 angle above which arm is
//                      considered "raised forward enough" (default 0.6)
//   elbow_safe_threshold_rad: elbow_2 angle above which arm is
//                      considered "bent forward enough" (default 0.9)

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <algorithm>
#include <mutex>
#include <atomic>

class TorsoSafetyGuard : public rclcpp::Node
{
public:
  TorsoSafetyGuard() : Node("torso_safety_guard")
  {
    declare_parameter<double>("safe_min_torso_z",            0.30);
    declare_parameter<double>("shoulder_safe_threshold_rad", 0.6);
    declare_parameter<double>("elbow_safe_threshold_rad",    0.9);
    declare_parameter<double>("max_torso_z",                 0.39);
    declare_parameter<bool>("verbose",                       true);
    refresh_params();

    param_cb_ = add_on_set_parameters_callback(
      [this](const std::vector<rclcpp::Parameter>&) {
        params_dirty_.store(true);
        rcl_interfaces::msg::SetParametersResult r;
        r.successful = true;
        return r;
      });

    safe_pub_ = create_publisher<std_msgs::msg::Float64MultiArray>(
      "/torso_position_controller/commands_safe", 10);

    cmd_sub_ = create_subscription<std_msgs::msg::Float64MultiArray>(
      "/torso_position_controller/commands", 10,
      [this](std_msgs::msg::Float64MultiArray::SharedPtr msg) {
        if (msg->data.empty()) return;
        if (params_dirty_.exchange(false)) refresh_params();

        double requested = msg->data[0];

        // First clamp to physical joint range (0 → max_torso_z)
        double range_clamped = std::clamp(requested, -0.6, max_torso_z_);
        bool was_range_clamped = std::abs(range_clamped - requested) > 1e-4;

        // Then apply arm-safety clamp
        double final_value = arm_safety_clamp(range_clamped);
        bool was_arm_clamped = std::abs(final_value - range_clamped) > 1e-4;

        std_msgs::msg::Float64MultiArray out;
        out.data = {final_value};
        safe_pub_->publish(out);

        if (verbose_) {
          if (was_arm_clamped) {
            RCLCPP_WARN(get_logger(),
              "Torso command %.3f BLOCKED → %.3f (arms in unsafe pose)",
              requested, final_value);
          } else if (was_range_clamped) {
            RCLCPP_INFO(get_logger(),
              "Torso command %.3f clamped to physical range → %.3f",
              requested, final_value);
          } else {
            RCLCPP_INFO(get_logger(),
              "Torso command %.3f passed through", requested);
          }
        }
      });

    state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
      "/joint_states", rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::JointState::SharedPtr msg) {
        std::lock_guard<std::mutex> lk(state_mutex_);
        for (size_t i = 0; i < msg->name.size(); ++i) {
          if (msg->name[i] == "left_shoulder" || msg->name[i] == "shoulder_link_1") l_shoulder1_ = msg->position[i];
          if (msg->name[i] == "left_forearm")    l_elbow2_    = msg->position[i];
          if (msg->name[i] == "right_shoulder" || msg->name[i] == "right_shoulder_1")  r_shoulder1_ = msg->position[i];
          if (msg->name[i] == "right_forearm")   r_elbow2_    = msg->position[i];
          if (msg->name[i] == "slider_z_axis" || msg->name[i] == "torso_joint")   torso_pos_   = msg->position[i];
        }
        have_state_ = true;
      });

    // ── Startup auto-raise (repeating until confirmed) ──
    // The arms hang down by default. With the torso at min height,
    // the arm tips dip below the base top. Auto-raise the torso to its
    // max position so the arms don't collide with the base.
    //
    // We start at 3s (after the 5s delayed controller spawners have had
    // a chance to activate) and KEEP re-publishing every 500ms until
    // /joint_states confirms the torso has actually started moving.
    // This eliminates the race condition where a single one-shot message
    // could be lost before the effort controller or PID were ready.
    startup_raise_timer_ = create_wall_timer(
      std::chrono::milliseconds(500),
      [this]() {
        startup_ticks_++;
        // Wait at least 6 ticks (3 seconds) for controllers to spawn
        if (startup_ticks_ < 6) return;

        // Check if torso has already responded (position moving up)
        double torso_pos = 0.0;
        {
          std::lock_guard<std::mutex> lk(state_mutex_);
          torso_pos = torso_pos_;
        }

        // Stop once the torso is above -0.3 (it has started moving)
        // or after 60 attempts (30s) to avoid infinite retries
        if ((have_state_ && torso_pos > -0.3) || startup_ticks_ > 120) {
          if (!sent_startup_) {
            sent_startup_ = true;
            RCLCPP_INFO(get_logger(),
              "Startup auto-raise complete: torso at %.3f m", torso_pos);
          }
          return;
        }

        double target = get_parameter("max_torso_z").as_double();
        std_msgs::msg::Float64MultiArray msg;
        msg.data = {target};
        safe_pub_->publish(msg);
        RCLCPP_INFO_THROTTLE(get_logger(), *get_clock(), 2000,
          "Startup auto-raise: publishing torso → %.3f m (tick %d, current pos=%.3f)",
          target, startup_ticks_, torso_pos);
      });

    RCLCPP_INFO(get_logger(),
      "Torso safety guard active. safe_min=%.2f, sh_thresh=%.2f, el_thresh=%.2f",
      safe_min_, shoulder_thresh_, elbow_thresh_);
  }

private:
  void refresh_params()
  {
    safe_min_         = get_parameter("safe_min_torso_z").as_double();
    shoulder_thresh_  = get_parameter("shoulder_safe_threshold_rad").as_double();
    elbow_thresh_     = get_parameter("elbow_safe_threshold_rad").as_double();
    max_torso_z_      = get_parameter("max_torso_z").as_double();
    verbose_          = get_parameter("verbose").as_bool();
  }

  // Returns true if the given arm is in a pose that's safe to lower the torso
  bool arm_is_safe(double shoulder1, double elbow2) const
  {
    // Arm is safe if EITHER:
    //   • shoulder_1 is raised enough forward (positive angle = arm forward/up)
    //   • elbow_2 is bent enough (forearm folded forward, hand high)
    // Both conditions check against |angle| since either positive raise
    // forward or backward (with our axis convention, positive = forward) is OK.
    return (std::abs(shoulder1) > shoulder_thresh_) ||
           (std::abs(elbow2)    > elbow_thresh_);
  }

  // Returns the value clamped only by arm-safety considerations.
  // Caller is expected to have already clamped to the physical range.
  double arm_safety_clamp(double value) const
  {
    // If we don't have arm state yet, be conservative — only allow above safe_min
    if (!have_state_) {
      return std::max(value, safe_min_);
    }

    double l_sh, l_el, r_sh, r_el;
    {
      std::lock_guard<std::mutex> lk(state_mutex_);
      l_sh = l_shoulder1_; l_el = l_elbow2_;
      r_sh = r_shoulder1_; r_el = r_elbow2_;
    }

    bool left_safe  = arm_is_safe(l_sh, l_el);
    bool right_safe = arm_is_safe(r_sh, r_el);

    if (left_safe && right_safe) return value;
    return std::max(value, safe_min_);
  }

  // Cached params
  double safe_min_{0.30};
  double shoulder_thresh_{0.6};
  double elbow_thresh_{0.9};
  double max_torso_z_{0.39};
  bool   verbose_{true};
  std::atomic<bool> params_dirty_{false};

  // Arm state
  mutable std::mutex state_mutex_;
  double l_shoulder1_{0.0}, l_elbow2_{0.0};
  double r_shoulder1_{0.0}, r_elbow2_{0.0};
  double torso_pos_{-1.0};  // track torso position for startup confirmation
  bool   have_state_{false};

  rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr cmd_sub_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr     state_sub_;
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr    safe_pub_;
  rclcpp::TimerBase::SharedPtr                                      startup_raise_timer_;
  OnSetParametersCallbackHandle::SharedPtr                          param_cb_;
  bool sent_startup_{false};
  int  startup_ticks_{0};
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TorsoSafetyGuard>());
  rclcpp::shutdown();
  return 0;
}
