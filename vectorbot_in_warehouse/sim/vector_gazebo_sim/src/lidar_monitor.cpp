/**
 * lidar_monitor.cpp — Livox Mid-360 LiDAR diagnostic / feedback node.
 *
 * Subscribes to:
 *   /livox_mid360/scan          (sensor_msgs/LaserScan)
 *   /livox_mid360/points        (sensor_msgs/PointCloud2)
 *   /livox_mid360/imu           (sensor_msgs/Imu)
 *
 * Publishes:
 *   /livox_mid360/diagnostics   (std_msgs/String, JSON blob with stats)
 *
 * Logs periodic summaries at a configurable rate (default 1 Hz) with:
 *   - Point cloud: total points, min/max/mean range, nearest obstacle
 *   - LaserScan:   valid ranges, min range + angle, coverage %
 *   - IMU:         linear accel, angular vel summaries
 *   - Timing:      message rates, latency estimates
 *
 * Parameters:
 *   log_rate_hz        (double, default 1.0)  — how often to print logs
 *   warn_min_range_m   (double, default 0.3)  — warn if obstacle closer
 *   warn_no_data_sec   (double, default 3.0)  — warn if no data for N sec
 */

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <std_msgs/msg/string.hpp>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <sstream>
#include <iomanip>

using namespace std::chrono_literals;

class LidarMonitor : public rclcpp::Node
{
public:
  LidarMonitor() : Node("lidar_monitor")
  {
    // ── Parameters ──────────────────────────────────────────────────
    declare_parameter("log_rate_hz",       1.0);
    declare_parameter("warn_min_range_m",  0.3);
    declare_parameter("warn_no_data_sec",  3.0);

    log_rate_hz_      = get_parameter("log_rate_hz").as_double();
    warn_min_range_m_ = get_parameter("warn_min_range_m").as_double();
    warn_no_data_sec_ = get_parameter("warn_no_data_sec").as_double();

    // ── Subscribers ─────────────────────────────────────────────────
    scan_sub_ = create_subscription<sensor_msgs::msg::LaserScan>(
      "/livox_mid360/scan", rclcpp::SensorDataQoS(),
      [this](const sensor_msgs::msg::LaserScan::SharedPtr msg) { on_scan(msg); });

    cloud_sub_ = create_subscription<sensor_msgs::msg::PointCloud2>(
      "/livox_mid360/points", rclcpp::SensorDataQoS(),
      [this](const sensor_msgs::msg::PointCloud2::SharedPtr msg) { on_cloud(msg); });

    imu_sub_ = create_subscription<sensor_msgs::msg::Imu>(
      "/livox_mid360/imu", rclcpp::SensorDataQoS(),
      [this](const sensor_msgs::msg::Imu::SharedPtr msg) { on_imu(msg); });

    // ── Publisher ───────────────────────────────────────────────────
    diag_pub_ = create_publisher<std_msgs::msg::String>(
      "/livox_mid360/diagnostics", 10);

    // ── Periodic log timer ──────────────────────────────────────────
    auto period_ms = static_cast<int>(1000.0 / std::max(log_rate_hz_, 0.1));
    timer_ = create_wall_timer(
      std::chrono::milliseconds(period_ms),
      [this]() { publish_diagnostics(); });

    RCLCPP_INFO(get_logger(),
      "Livox Mid-360 monitor started  [log_rate=%.1f Hz, "
      "warn_min_range=%.2f m, warn_no_data=%.1f s]",
      log_rate_hz_, warn_min_range_m_, warn_no_data_sec_);
  }

private:
  // ── Scan callback ─────────────────────────────────────────────────
  void on_scan(const sensor_msgs::msg::LaserScan::SharedPtr msg)
  {
    last_scan_time_ = now();
    scan_count_++;

    // Compute scan statistics
    int valid = 0;
    float min_r = msg->range_max;
    float max_r = 0.0f;
    double sum_r = 0.0;
    float min_r_angle = 0.0f;

    for (size_t i = 0; i < msg->ranges.size(); ++i) {
      float r = msg->ranges[i];
      if (std::isfinite(r) && r >= msg->range_min && r <= msg->range_max) {
        valid++;
        sum_r += r;
        if (r < min_r) {
          min_r = r;
          min_r_angle = msg->angle_min + i * msg->angle_increment;
        }
        if (r > max_r) max_r = r;
      }
    }

    scan_valid_count_  = valid;
    scan_total_count_  = static_cast<int>(msg->ranges.size());
    scan_min_range_    = min_r;
    scan_max_range_    = max_r;
    scan_mean_range_   = (valid > 0) ? sum_r / valid : 0.0;
    scan_min_angle_    = min_r_angle;
    scan_coverage_pct_ = (msg->ranges.size() > 0)
      ? 100.0 * valid / msg->ranges.size() : 0.0;

    // Proximity warning
    if (min_r < warn_min_range_m_ && valid > 0) {
      RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 2000,
        "⚠ OBSTACLE at %.2f m (angle %.1f°)",
        min_r, min_r_angle * 180.0 / M_PI);
    }
  }

  // ── Point cloud callback ──────────────────────────────────────────
  void on_cloud(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    last_cloud_time_ = now();
    cloud_count_++;
    cloud_point_count_ = msg->width * msg->height;
    cloud_data_bytes_  = msg->data.size();
  }

  // ── IMU callback ──────────────────────────────────────────────────
  void on_imu(const sensor_msgs::msg::Imu::SharedPtr msg)
  {
    last_imu_time_ = now();
    imu_count_++;

    imu_accel_x_ = msg->linear_acceleration.x;
    imu_accel_y_ = msg->linear_acceleration.y;
    imu_accel_z_ = msg->linear_acceleration.z;
    imu_gyro_x_  = msg->angular_velocity.x;
    imu_gyro_y_  = msg->angular_velocity.y;
    imu_gyro_z_  = msg->angular_velocity.z;
  }

  // ── Periodic diagnostics ──────────────────────────────────────────
  void publish_diagnostics()
  {
    auto t_now = now();
    double dt = (t_now - last_diag_time_).seconds();
    if (dt < 0.01) dt = 1.0;  // avoid div-by-zero on first tick

    // Compute message rates
    double scan_hz  = (scan_count_ - prev_scan_count_) / dt;
    double cloud_hz = (cloud_count_ - prev_cloud_count_) / dt;
    double imu_hz   = (imu_count_ - prev_imu_count_) / dt;

    prev_scan_count_  = scan_count_;
    prev_cloud_count_ = cloud_count_;
    prev_imu_count_   = imu_count_;
    last_diag_time_   = t_now;

    // Check for data timeouts
    bool scan_timeout  = scan_count_ > 0 &&
      (t_now - last_scan_time_).seconds() > warn_no_data_sec_;
    bool cloud_timeout = cloud_count_ > 0 &&
      (t_now - last_cloud_time_).seconds() > warn_no_data_sec_;

    if (scan_timeout) {
      RCLCPP_WARN(get_logger(),
        "⚠ No LaserScan data for %.1f s!", (t_now - last_scan_time_).seconds());
    }
    if (cloud_timeout) {
      RCLCPP_WARN(get_logger(),
        "⚠ No PointCloud2 data for %.1f s!", (t_now - last_cloud_time_).seconds());
    }

    // First-run waiting message
    if (scan_count_ == 0 && cloud_count_ == 0) {
      RCLCPP_INFO_THROTTLE(get_logger(), *get_clock(), 5000,
        "Waiting for Livox Mid-360 data...");
      return;
    }

    // ── Build JSON diagnostics ────────────────────────────────────
    std::ostringstream json;
    json << std::fixed << std::setprecision(3);
    json << "{";
    json << "\"scan\":{";
    json <<   "\"rate_hz\":" << scan_hz << ",";
    json <<   "\"valid_rays\":" << scan_valid_count_ << ",";
    json <<   "\"total_rays\":" << scan_total_count_ << ",";
    json <<   "\"coverage_pct\":" << scan_coverage_pct_ << ",";
    json <<   "\"min_range_m\":" << scan_min_range_ << ",";
    json <<   "\"max_range_m\":" << scan_max_range_ << ",";
    json <<   "\"mean_range_m\":" << scan_mean_range_ << ",";
    json <<   "\"nearest_angle_deg\":" << (scan_min_angle_ * 180.0 / M_PI);
    json << "},";
    json << "\"cloud\":{";
    json <<   "\"rate_hz\":" << cloud_hz << ",";
    json <<   "\"points\":" << cloud_point_count_ << ",";
    json <<   "\"data_kb\":" << (cloud_data_bytes_ / 1024);
    json << "},";
    json << "\"imu\":{";
    json <<   "\"rate_hz\":" << imu_hz << ",";
    json <<   "\"accel\":[" << imu_accel_x_ << "," << imu_accel_y_ << "," << imu_accel_z_ << "],";
    json <<   "\"gyro\":[" << imu_gyro_x_ << "," << imu_gyro_y_ << "," << imu_gyro_z_ << "]";
    json << "},";
    json << "\"status\":\"" << (scan_timeout || cloud_timeout ? "WARN" : "OK") << "\"";
    json << "}";

    // Publish diagnostics
    auto diag_msg = std_msgs::msg::String();
    diag_msg.data = json.str();
    diag_pub_->publish(diag_msg);

    // ── Console log ───────────────────────────────────────────────
    RCLCPP_INFO(get_logger(),
      "━━━ Livox Mid-360 ━━━  scan: %.1f Hz (%d/%d rays, %.0f%% coverage)  "
      "nearest: %.2f m @ %.0f°  |  cloud: %.1f Hz (%d pts, %zu KB)  "
      "|  imu: %.0f Hz  accel=[%.2f,%.2f,%.2f]",
      scan_hz, scan_valid_count_, scan_total_count_, scan_coverage_pct_,
      scan_min_range_, scan_min_angle_ * 180.0 / M_PI,
      cloud_hz, cloud_point_count_, cloud_data_bytes_ / 1024,
      imu_hz, imu_accel_x_, imu_accel_y_, imu_accel_z_);
  }

  // ── Parameters ──────────────────────────────────────────────────
  double log_rate_hz_{1.0};
  double warn_min_range_m_{0.3};
  double warn_no_data_sec_{3.0};

  // ── Subscribers / Publishers ──────────────────────────────────────
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr cloud_sub_;
  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr diag_pub_;
  rclcpp::TimerBase::SharedPtr timer_;

  // ── Scan stats ────────────────────────────────────────────────────
  int    scan_valid_count_{0};
  int    scan_total_count_{0};
  float  scan_min_range_{0.0f};
  float  scan_max_range_{0.0f};
  double scan_mean_range_{0.0};
  float  scan_min_angle_{0.0f};
  double scan_coverage_pct_{0.0};

  // ── Cloud stats ───────────────────────────────────────────────────
  int    cloud_point_count_{0};
  size_t cloud_data_bytes_{0};

  // ── IMU state ─────────────────────────────────────────────────────
  double imu_accel_x_{0}, imu_accel_y_{0}, imu_accel_z_{0};
  double imu_gyro_x_{0},  imu_gyro_y_{0},  imu_gyro_z_{0};

  // ── Counters & timing ─────────────────────────────────────────────
  uint64_t scan_count_{0},  prev_scan_count_{0};
  uint64_t cloud_count_{0}, prev_cloud_count_{0};
  uint64_t imu_count_{0},   prev_imu_count_{0};

  rclcpp::Time last_scan_time_{0, 0, RCL_ROS_TIME};
  rclcpp::Time last_cloud_time_{0, 0, RCL_ROS_TIME};
  rclcpp::Time last_imu_time_{0, 0, RCL_ROS_TIME};
  rclcpp::Time last_diag_time_{0, 0, RCL_ROS_TIME};
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<LidarMonitor>());
  rclcpp::shutdown();
  return 0;
}
