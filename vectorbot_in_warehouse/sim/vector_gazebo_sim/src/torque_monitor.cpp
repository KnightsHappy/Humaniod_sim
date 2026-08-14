// torque_monitor.cpp
//
// Joint torque (effort) feedback monitor for the Vector robot.
//
// Purpose:
//   Reads the effort field from /joint_states (published by joint_state_broadcaster)
//   and provides torque data through multiple channels for analytics:
//     1. ROS topic (JSON)  — real-time, any subscriber can consume
//     2. Console logs      — human-readable periodic summaries
//     3. CSV file          — timestamped offline analysis (optional)
//
// Architecture:
//   /joint_states (sensor_msgs/JointState)
//        │  — published by joint_state_broadcaster at 50 Hz
//        │  — includes .effort[] for every joint with effort state_interface
//        ▼
//   torque_monitor (this node)
//        │
//        ├──→ /torque_monitor/joint_efforts   (std_msgs/String, JSON)
//        │       Per-joint effort + position + velocity every publish tick
//        │       Subscribe from any analytics plugin (Python, C++, MATLAB bridge)
//        │
//        ├──→ /torque_monitor/diagnostics     (std_msgs/String, JSON)
//        │       Summary: max effort joint, total, anomaly flags
//        │       Dashboard-ready, same rate as joint_efforts
//        │
//        ├──→ Console logs (configurable rate)
//        │       Human-readable one-liner with key stats
//        │
//        └──→ CSV file (optional, enable via parameter)
//                Append-mode, one row per joint per sample
//                Path configurable at runtime
//
// Parameters (all live-tunable via ros2 param set):
//   log_rate_hz           (double, 2.0)    — console print frequency
//   publish_rate_hz       (double, 10.0)   — topic publish frequency
//   enable_csv_log        (bool,  false)   — write CSV file
//   csv_path              (string, /tmp/vector_torque_log.csv)
//   warn_effort_threshold (double, 50.0)   — warn if |effort| exceeds this
//
// Extension points for future analytics:
//   • Subscribe to /torque_monitor/joint_efforts for real-time data
//   • Parse JSON with any language (Python json module, C++ nlohmann, etc.)
//   • Post-process CSV with pandas, MATLAB, Excel
//   • Add your own subscriber node — this node is read-only, never modifies
//     the control pipeline

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_msgs/msg/string.hpp>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <mutex>
#include <sstream>
#include <string>
#include <vector>

using namespace std::chrono_literals;

class TorqueMonitor : public rclcpp::Node
{
public:
  TorqueMonitor() : Node("torque_monitor")
  {
    // ── Parameters ──────────────────────────────────────────────────
    declare_parameter<double>("log_rate_hz",           2.0);
    declare_parameter<double>("publish_rate_hz",       10.0);
    declare_parameter<bool>("enable_csv_log",          false);
    declare_parameter<std::string>("csv_path",         "/tmp/vector_torque_log.csv");
    declare_parameter<double>("warn_effort_threshold", 50.0);

    refresh_params();

    // Parameter change callback — live tuning support
    param_cb_ = add_on_set_parameters_callback(
      [this](const std::vector<rclcpp::Parameter>& /*params*/) {
        params_dirty_.store(true);
        rcl_interfaces::msg::SetParametersResult result;
        result.successful = true;
        return result;
      });

    // ── Subscription ────────────────────────────────────────────────
    state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
      "/joint_states", rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::JointState::SharedPtr msg) {
        on_joint_state(msg);
      });

    // ── Publishers ──────────────────────────────────────────────────
    efforts_pub_ = create_publisher<std_msgs::msg::String>(
      "/torque_monitor/joint_efforts", 10);
    diag_pub_ = create_publisher<std_msgs::msg::String>(
      "/torque_monitor/diagnostics", 10);

    // ── Publish timer ───────────────────────────────────────────────
    auto pub_period_ms = static_cast<int>(1000.0 / std::max(publish_rate_hz_, 0.1));
    publish_timer_ = create_wall_timer(
      std::chrono::milliseconds(pub_period_ms),
      [this]() { publish_data(); });

    // ── Log timer (separate, usually slower) ────────────────────────
    auto log_period_ms = static_cast<int>(1000.0 / std::max(log_rate_hz_, 0.1));
    log_timer_ = create_wall_timer(
      std::chrono::milliseconds(log_period_ms),
      [this]() { log_summary(); });

    RCLCPP_INFO(get_logger(),
      "Torque monitor started  [pub=%.1f Hz, log=%.1f Hz, csv=%s, threshold=%.1f]",
      publish_rate_hz_, log_rate_hz_,
      enable_csv_ ? "ON" : "OFF", warn_threshold_);
    RCLCPP_INFO(get_logger(),
      "Topics: /torque_monitor/joint_efforts, /torque_monitor/diagnostics");
    RCLCPP_INFO(get_logger(),
      "Live tune: ros2 param set /torque_monitor <param> <value>");
  }

private:
  // ── Joint state callback ────────────────────────────────────────────
  void on_joint_state(const sensor_msgs::msg::JointState::SharedPtr msg)
  {
    std::lock_guard<std::mutex> lk(data_mutex_);
    joint_names_  = msg->name;
    positions_    = msg->position;
    velocities_   = msg->velocity;
    efforts_      = msg->effort;
    have_data_    = true;
    msg_count_++;

    // Write CSV if enabled (every incoming message for full resolution)
    if (enable_csv_ && !csv_path_.empty()) {
      write_csv_row(msg);
    }
  }

  // ── Publish JSON data on topics ─────────────────────────────────────
  void publish_data()
  {
    // Lazy parameter refresh
    if (params_dirty_.exchange(false)) {
      refresh_params();
      RCLCPP_INFO(get_logger(),
        "Params updated: pub=%.1f Hz, log=%.1f Hz, csv=%s, threshold=%.1f",
        publish_rate_hz_, log_rate_hz_,
        enable_csv_ ? "ON" : "OFF", warn_threshold_);
    }

    if (!have_data_) {
      RCLCPP_INFO_THROTTLE(get_logger(), *get_clock(), 5000,
        "Waiting for /joint_states effort data...");
      return;
    }

    // Snapshot current state
    std::vector<std::string> names;
    std::vector<double> pos, vel, eff;
    {
      std::lock_guard<std::mutex> lk(data_mutex_);
      names = joint_names_;
      pos   = positions_;
      vel   = velocities_;
      eff   = efforts_;
    }

    // ── Build per-joint JSON ──────────────────────────────────────
    std::ostringstream json;
    json << std::fixed << std::setprecision(4);

    double sim_time = now().seconds();
    json << "{\"timestamp\":" << std::setprecision(3) << sim_time << ",";
    json << "\"joints\":{";

    double max_abs_effort = 0.0;
    std::string max_effort_joint;
    double total_abs_effort = 0.0;
    std::vector<std::string> over_threshold;

    for (size_t i = 0; i < names.size(); ++i) {
      double p = (i < pos.size()) ? pos[i] : 0.0;
      double v = (i < vel.size()) ? vel[i] : 0.0;
      double e = (i < eff.size()) ? eff[i] : 0.0;

      if (i > 0) json << ",";
      json << std::setprecision(4);
      json << "\"" << names[i] << "\":{";
      json << "\"effort\":" << e << ",";
      json << "\"position\":" << p << ",";
      json << "\"velocity\":" << v << "}";

      double abs_e = std::abs(e);
      total_abs_effort += abs_e;
      if (abs_e > max_abs_effort) {
        max_abs_effort = abs_e;
        max_effort_joint = names[i];
      }
      if (abs_e > warn_threshold_) {
        over_threshold.push_back(names[i]);
      }
    }
    json << "}}";

    auto efforts_msg = std_msgs::msg::String();
    efforts_msg.data = json.str();
    efforts_pub_->publish(efforts_msg);

    // ── Build diagnostics JSON ────────────────────────────────────
    std::ostringstream diag;
    diag << std::fixed << std::setprecision(3);
    diag << "{\"timestamp\":" << sim_time << ",";
    diag << "\"max_effort_joint\":\"" << max_effort_joint << "\",";
    diag << "\"max_effort_value\":" << max_abs_effort << ",";
    diag << "\"total_abs_effort\":" << total_abs_effort << ",";
    diag << "\"joints_over_threshold\":[";
    for (size_t i = 0; i < over_threshold.size(); ++i) {
      if (i > 0) diag << ",";
      diag << "\"" << over_threshold[i] << "\"";
    }
    diag << "],";
    diag << "\"status\":\"" << (over_threshold.empty() ? "OK" : "WARN") << "\"}";

    auto diag_msg = std_msgs::msg::String();
    diag_msg.data = diag.str();
    diag_pub_->publish(diag_msg);

    // Cache for log_summary
    {
      std::lock_guard<std::mutex> lk(stats_mutex_);
      last_max_joint_    = max_effort_joint;
      last_max_effort_   = max_abs_effort;
      last_total_effort_ = total_abs_effort;
      last_over_         = over_threshold;
    }
  }

  // ── Console log summary ─────────────────────────────────────────────
  void log_summary()
  {
    if (!have_data_) return;

    std::string max_joint;
    double max_eff, total_eff;
    std::vector<std::string> over;
    {
      std::lock_guard<std::mutex> lk(stats_mutex_);
      max_joint = last_max_joint_;
      max_eff   = last_max_effort_;
      total_eff = last_total_effort_;
      over      = last_over_;
    }

    uint64_t rate_count;
    {
      std::lock_guard<std::mutex> lk(data_mutex_);
      rate_count = msg_count_ - prev_msg_count_;
      prev_msg_count_ = msg_count_;
    }

    if (over.empty()) {
      RCLCPP_INFO(get_logger(),
        "━━━ Torque ━━━  max: %s %.2f  |  total: %.1f  |  rate: %lu Hz  |  csv: %s  |  OK",
        max_joint.c_str(), max_eff, total_eff,
        static_cast<unsigned long>(rate_count * static_cast<uint64_t>(log_rate_hz_)),
        enable_csv_ ? "ON" : "OFF");
    } else {
      std::string over_str;
      for (size_t i = 0; i < over.size(); ++i) {
        if (i > 0) over_str += ",";
        over_str += over[i];
      }
      RCLCPP_WARN(get_logger(),
        "━━━ Torque ━━━  max: %s %.2f  |  total: %.1f  |  OVER THRESHOLD: [%s]  |  csv: %s",
        max_joint.c_str(), max_eff, total_eff, over_str.c_str(),
        enable_csv_ ? "ON" : "OFF");
    }
  }

  // ── CSV writer ──────────────────────────────────────────────────────
  void write_csv_row(const sensor_msgs::msg::JointState::SharedPtr& msg)
  {
    // Open file on first write (or reopen if path changed)
    if (!csv_file_.is_open() || csv_current_path_ != csv_path_) {
      if (csv_file_.is_open()) csv_file_.close();
      csv_file_.open(csv_path_, std::ios::app);
      csv_current_path_ = csv_path_;
      if (!csv_file_.is_open()) {
        RCLCPP_ERROR_THROTTLE(get_logger(), *get_clock(), 10000,
          "Cannot open CSV file: %s", csv_path_.c_str());
        return;
      }
      // Write header if file is empty (newly created)
      csv_file_.seekp(0, std::ios::end);
      if (csv_file_.tellp() == 0) {
        csv_file_ << "timestamp,joint_name,position,velocity,effort\n";
      }
      RCLCPP_INFO(get_logger(), "CSV logging to: %s", csv_path_.c_str());
    }

    double t = now().seconds();
    for (size_t i = 0; i < msg->name.size(); ++i) {
      double p = (i < msg->position.size()) ? msg->position[i] : 0.0;
      double v = (i < msg->velocity.size()) ? msg->velocity[i] : 0.0;
      double e = (i < msg->effort.size())   ? msg->effort[i]   : 0.0;
      csv_file_ << std::fixed << std::setprecision(4)
                << t << "," << msg->name[i] << ","
                << p << "," << v << "," << e << "\n";
    }
    csv_file_.flush();
  }

  // ── Parameter refresh ───────────────────────────────────────────────
  void refresh_params()
  {
    log_rate_hz_     = get_parameter("log_rate_hz").as_double();
    publish_rate_hz_ = get_parameter("publish_rate_hz").as_double();
    enable_csv_      = get_parameter("enable_csv_log").as_bool();
    csv_path_        = get_parameter("csv_path").as_string();
    warn_threshold_  = get_parameter("warn_effort_threshold").as_double();

    // Close CSV if logging was disabled
    if (!enable_csv_ && csv_file_.is_open()) {
      csv_file_.close();
      RCLCPP_INFO(get_logger(), "CSV logging disabled, file closed.");
    }
  }

  // ── Cached parameter values ─────────────────────────────────────────
  double log_rate_hz_{2.0};
  double publish_rate_hz_{10.0};
  bool   enable_csv_{false};
  std::string csv_path_{"/tmp/vector_torque_log.csv"};
  double warn_threshold_{50.0};
  std::atomic<bool> params_dirty_{false};

  // ── Latest joint state (protected by data_mutex_) ───────────────────
  std::mutex data_mutex_;
  std::vector<std::string> joint_names_;
  std::vector<double> positions_, velocities_, efforts_;
  bool     have_data_{false};
  uint64_t msg_count_{0}, prev_msg_count_{0};

  // ── Cached stats for log_summary (protected by stats_mutex_) ────────
  std::mutex stats_mutex_;
  std::string last_max_joint_;
  double last_max_effort_{0.0};
  double last_total_effort_{0.0};
  std::vector<std::string> last_over_;

  // ── CSV output ──────────────────────────────────────────────────────
  std::ofstream csv_file_;
  std::string csv_current_path_;

  // ── ROS handles ─────────────────────────────────────────────────────
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr state_sub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr            efforts_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr            diag_pub_;
  rclcpp::TimerBase::SharedPtr                                   publish_timer_;
  rclcpp::TimerBase::SharedPtr                                   log_timer_;
  OnSetParametersCallbackHandle::SharedPtr                       param_cb_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TorqueMonitor>());
  rclcpp::shutdown();
  return 0;
}
