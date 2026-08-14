cmake_minimum_required(VERSION 3.8)
project(vector_gazebo_sim)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

# C++ Twist→TwistStamped bridge — converts OS plain Twist to TwistStamped
# (Jazzy diff_drive_controller requires TwistStamped on /base_controller/cmd_vel)
add_executable(twist_to_stamped src/twist_to_stamped.cpp)
ament_target_dependencies(twist_to_stamped rclcpp geometry_msgs)

# C++ position-PID for torso — works around gz_ros2_control issue #192
# by running a software PID and outputting effort instead of position.
# See src/torso_position_pid.cpp for full architecture explanation.
add_executable(torso_position_pid src/torso_position_pid.cpp)
ament_target_dependencies(torso_position_pid rclcpp std_msgs sensor_msgs)

# C++ arm-collision-aware torso safety guard — intercepts torso commands
# and refuses descent when arms are in a pose that would collide with base.
# See src/torso_safety_guard.cpp for safety logic.
add_executable(torso_safety_guard src/torso_safety_guard.cpp)
ament_target_dependencies(torso_safety_guard rclcpp std_msgs sensor_msgs)

# C++ teleop bridge — converts Gazebo Teleop Q/E keys (linear.z in /cmd_vel)
# into torso position commands on /torso_position_controller/commands.
add_executable(torso_teleop_bridge src/torso_teleop_bridge.cpp)
ament_target_dependencies(torso_teleop_bridge rclcpp geometry_msgs std_msgs)

# Livox Mid-360 LiDAR diagnostic monitor — logs scan stats, point cloud
# density, IMU data, and obstacle proximity warnings.
add_executable(lidar_monitor src/lidar_monitor.cpp)
ament_target_dependencies(lidar_monitor rclcpp sensor_msgs std_msgs)

# Joint torque feedback monitor — reads effort from /joint_states,
# publishes JSON on /torque_monitor/* topics, optionally logs CSV.
# See src/torque_monitor.cpp for full architecture.
add_executable(torque_monitor src/torque_monitor.cpp)
ament_target_dependencies(torque_monitor rclcpp std_msgs sensor_msgs)

install(
  TARGETS twist_to_stamped torso_position_pid torso_safety_guard torso_teleop_bridge lidar_monitor torque_monitor
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY config launch worlds 
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
