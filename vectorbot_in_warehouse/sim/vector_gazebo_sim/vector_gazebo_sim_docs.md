# vector_gazebo_sim

Gazebo Harmonic simulation package for the Vector humanoid robot. Provides a drop-in replacement for the real hardware interfaces — the OS stack launches unchanged and all `ros2_control` topics remain identical to the physical robot.

---

## Installation

### Prerequisites

| Requirement | Version |
|---|---|
| Ubuntu | 24.04 |
| ROS 2 | Jazzy Jalisco |
| Gazebo | Harmonic |

Install system dependencies:

```bash
sudo apt install \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-ros-gz-image \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-controller-manager \
  ros-jazzy-joint-state-broadcaster \
  ros-jazzy-joint-trajectory-controller \
  ros-jazzy-effort-controllers \
  ros-jazzy-velocity-controllers \
  ros-jazzy-diff-drive-controller \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-xacro \
  ros-jazzy-rviz2 \
  ros-jazzy-topic-tools
```

### Cloning the repository

The package lives on the `industrial_robot_simulation` branch of the Vector Robotics sim repo:

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone -b industrial_robot_simulation https://github.com/Vector-Robotics/sim.git
# The package is at sim/vector_gazebo_sim
```

### Building

```bash
cd ~/ros2_ws
colcon build --packages-select vector_gazebo_sim
source install/setup.bash
```

---

## Running the Simulation

The full stack requires four terminals. Source both workspaces in every terminal before running:

```bash
source ~/ros2_ws/install/setup.bash
source ~/vector_os/install/setup.bash
```

> `vector_navigation` and `robot_startup` live in `~/vector_os`. Only `vector_gazebo_sim` lives in `~/ros2_ws`.

### Terminal 1 — Simulation

```bash
ros2 launch vector_gazebo_sim sim.launch.py world:=warehouse.sdf
```

Wait until you see all four controllers activate in the terminal:

```
Configured and activated joint_state_broadcaster
Configured and activated base_controller
Configured and activated joint_trajectory_controller
Configured and activated torso_effort_controller
```

The torso auto-raises to its maximum position (~1.5 s after controller activation).

### Terminal 2 — Navigation Stack

```bash
ros2 launch vector_navigation gazebo_sim_nav.launch.py
```

### Terminal 3 — Robot OS

```bash
ros2 launch robot_startup main.launch.py use_sim:=true
```

### Terminal 4 — RViz

```bash
rviz2
```

**Recommended RViz display configuration:**

| Display | Topic / Setting |
|---|---|
| Fixed Frame | `base_link` |
| RobotModel | `/robot_description` |
| TF | — |
| Image | `/head_camera/image_raw` |
| PointCloud2 | `/head_camera/points` |
| LaserScan | `/base_lidar/scan` (Reliability: Best Effort) |
| LaserScan | `/spine_lidar/scan` (Reliability: Best Effort) |
| Pose | `/goal_pose` |
| Map | `/map` |

> **Normal behaviour:** RViz will show "No tf data" and "No Image" for approximately the first 10 seconds while Gazebo and the bridge initialise. This is expected.

### Quick standalone test (sim + RViz only)

```bash
ros2 launch vector_gazebo_sim test.launch.py world:=warehouse.sdf
```

Launches the simulation and opens RViz with the saved config in one command. Useful for verifying the robot model and sensors before bringing up the full OS stack.

---

## Launch Arguments

| Argument | Default | Description |
|---|---|---|
| `world` | `empty.sdf` | World file to load. Use `warehouse.sdf` for the full environment |
| `headless` | `false` | Run Gazebo without a GUI window (useful for CI or remote machines) |
| `launch_os` | `false` | Embed the OS (`vector_hardware_controllers`) launch directly inside this launch file |
| `os_ws` | `` | Path to the vector_os workspace root, used when `launch_os:=true` |

Examples:

```bash
# Headless (no GUI)
ros2 launch vector_gazebo_sim sim.launch.py world:=warehouse.sdf headless:=true

# Embed the OS in one command
ros2 launch vector_gazebo_sim sim.launch.py world:=warehouse.sdf launch_os:=true os_ws:=~/vector_os
```

---

## Package Structure

```
vector_gazebo_sim/
├── config/
│   ├── bridge.yaml               # ROS ↔ Gazebo topic bridges
│   └── gz_ros2_control_config.yaml  # Controller configs and parameters
├── launch/
│   ├── sim.launch.py             # Main launch file
│   └── test.launch.py            # Sim + RViz standalone test
├── src/
│   ├── twist_to_stamped.cpp      # Twist → TwistStamped bridge
│   ├── torso_position_pid.cpp    # Software PID for torso lift
│   └── torso_safety_guard.cpp    # Arm collision safety for torso
├── urdf/
│   └── vector_robot.urdf.xacro  # Full robot description
├── worlds/
│   ├── empty.sdf                 # Flat ground plane
│   └── warehouse.sdf             # Industrial warehouse environment
└── rviz/
    └── vector_sim.rviz           # Default RViz configuration
```

---

## Robot Description

The robot is defined in `urdf/vector_robot.urdf.xacro`. All dimensions are measured from the real robot.

### Kinematic Overview

```
base_footprint  (ground projection, z=0, URDF root)
└── base_link  (base box centre, z=0.185 m)
    ├── left_wheel_link    (continuous, velocity controlled)
    ├── right_wheel_link   (continuous, velocity controlled)
    ├── caster_link        (fixed, frictionless)
    └── torso_column_link  (fixed to base, does NOT move with lift)
        └── torso_platform_link  (prismatic torso_z_joint, effort controlled)
            ├── left_s1_link → left_s2_link → left_e1_link → left_e2_link
            │   → left_wrist_link → left_ee_link   (left arm, 6 DOF)
            ├── right_s1_link → ... → right_ee_link (right arm, 6 DOF)
            └── neck_pan_link  (revolute neck_horizontal)
                └── head_link  (revolute neck_vertical)
                    ├── camera_link        (fixed, head_to_camera)
                    └── camera_optical_frame (fixed, camera_to_optical)
```

### Physical Dimensions

| Component | Value |
|---|---|
| Base | 0.44 × 0.40 × 0.25 m |
| Ground clearance | 60 mm |
| Wheel diameter | 150 mm |
| Wheel separation (centre-to-centre) | 455 mm |
| Spine column height | 1.11 m |
| Torso lift travel | 0 – 390 mm |
| Torso platform min height (joint=0) | 715 mm above ground |
| Upper arm length | 270 mm |
| Forearm length | 220 mm |
| Head diameter | 160 mm |

### Joint Summary

| Joint | Type | Control |
|---|---|---|
| `left_wheel_joint` / `right_wheel_joint` | Continuous | Velocity (diff drive) |
| `torso_z_joint` | Prismatic | Effort (software PID) |
| `left/right_shoulder_1` | Revolute ±360° | Position (JTC) |
| `left/right_shoulder_2` | Revolute ±103° | Position (JTC) |
| `left/right_elbow_1` | Revolute ±360° | Position (JTC) |
| `left/right_elbow_2` | Revolute ±155° | Position (JTC) |
| `left/right_wrist_1` | Revolute ±135° | Position (JTC) |
| `left/right_wrist_2` | Revolute ±90° | Position (JTC) |
| `neck_horizontal` | Revolute ±90° | Position (JTC) |
| `neck_vertical` | Revolute ±40° | Position (JTC) |

---

## Controllers

Managed by `gz_ros2_control` at 50 Hz. Defined in `config/gz_ros2_control_config.yaml`.

### joint_state_broadcaster
Publishes all joint positions and velocities to `/joint_states`. Required by `robot_state_publisher` for TF.

### base_controller (DiffDriveController)
Controls the two drive wheels. Publishes odometry and the `odom → base_footprint` TF.

- Subscribes: `/base_controller/cmd_vel` (TwistStamped)
- Publishes: `/odom`, TF `odom → base_footprint`
- Base frame: `base_footprint` (important — using `base_link` would create a broken TF tree)

The OS publishes plain `Twist` on `/cmd_vel_final`. The `twist_to_stamped` C++ node bridges this to the `TwistStamped` format that Jazzy's `DiffDriveController` requires.

### joint_trajectory_controller (JTC)
Controls all 14 arm and neck joints via position interface.

- Subscribes: `/joint_trajectory_controller/joint_trajectory`
- `allow_partial_joints_goal: true` — the OS arm manager can send commands for a subset of joints without specifying all 14

Example — raise both arms:
```bash
ros2 topic pub --once /joint_trajectory_controller/joint_trajectory \
  trajectory_msgs/msg/JointTrajectory \
  "{joint_names: [left_shoulder_1, right_shoulder_1], \
    points: [{positions: [1.57, 1.57], time_from_start: {sec: 2}}]}"
```

### torso_effort_controller
Low-level effort (force) interface for `torso_z_joint`. Not commanded directly — receives output from the software PID node described below.

---

## Torso Lift System

The torso uses a three-layer control pipeline because `gz_ros2_control`'s position interface cannot lift a vertical prismatic joint against gravity (upstream issue #192).

```
OS publishes Float64MultiArray
    → /torso_position_controller/commands
        → torso_safety_guard     (arm collision check)
            → /torso_position_controller/commands_safe
                → torso_position_pid  (software PID + gravity FF)
                    → /torso_effort_controller/commands
                        → torso_effort_controller (ros2_control)
                            → torso_z_joint effort interface (Gazebo)
```

### torso_position_pid

Software PID node running at 50 Hz. Designed for a 13 kg payload with:

| Parameter | Value | Derivation |
|---|---|---|
| `kp` | 208 N/m | m·ωn² (m=13 kg, ωn=4 rad/s) |
| `kd` | 104 N·s/m | 2·ζ·m·ωn (ζ=1, critical damping) |
| `ki` | 0 | Feedforward handles steady state; I causes windup |
| `gravity_feedforward_n` | 127 N | m·g = 13 × 9.81 |
| `setpoint_slew_m_per_s` | 0.15 m/s | Prevents step-input transients |
| `deadband_m` | 1 mm | Suppresses micro-oscillation at rest |

All parameters are live-tunable:
```bash
ros2 param set /torso_position_pid kp 250.0
```

### torso_safety_guard

Intercepts torso commands before they reach the PID. Refuses to lower the torso below `safe_min_torso_z` (default 0.30 m) if either arm is hanging in a pose that would collide with the base.

An arm is considered **safe** if either:
- `|shoulder_1|` > 0.6 rad (arm raised forward or backward)
- `|elbow_2|` > 0.9 rad (forearm folded, hand above collision zone)

On startup, the guard auto-raises the torso to max (0.39 m) 1.5 s after launch, keeping arms clear of the base while controllers initialise.

Command the torso (range 0.0 – 0.39 m):
```bash
ros2 topic pub --once /torso_position_controller/commands \
  std_msgs/msg/Float64MultiArray "{data: [0.39]}"
```

---

## Sensors

### Base Lidar

360° GPU lidar mounted on top of the base, in front of the spine column.

| Property | Value |
|---|---|
| Height | 0.335 m above ground |
| Range | 0.10 – 15.0 m |
| Resolution | 360 samples / revolution |
| Rate | 10 Hz |
| ROS topic | `/base_lidar/scan` (sensor_msgs/LaserScan) |
| TF frame | `base_lidar_link` |

### Spine Lidar

360° GPU lidar mounted at the top of the fixed spine column. Provides a high-vantage scan above the torso and arms.

| Property | Value |
|---|---|
| Height | 1.445 m above ground |
| Range | 0.10 – 15.0 m |
| Resolution | 360 samples / revolution |
| Rate | 10 Hz |
| ROS topic | `/spine_lidar/scan` (sensor_msgs/LaserScan) |
| TF frame | `spine_lidar_link` |

> **Implementation note:** Both lidars are attached as Gazebo sensors on `base_footprint` (not on their respective URDF links) using pre-composed world poses. This is a workaround for sdformat's fixed-joint lumping behaviour, which merges fixed-jointed child links into the parent and drops sensor definitions. The URDF still declares the correct joint chain so `robot_state_publisher` publishes the right TF frames.

### Head Camera (OAK-D Lite style)

RGBD camera on the head, moves with neck pan + tilt and torso lift.

| Property | Value |
|---|---|
| Type | `rgbd_camera` (Gazebo) |
| Position | 0.10 m forward, 0.08 m above head_link origin |
| FOV | 81° horizontal (1.414 rad) — matches OAK-D Lite |
| Resolution | 640 × 480 |
| Depth range | 0.19 – 50.0 m |
| Rate | 15 Hz |
| gz_frame_id | `camera_link` |

Published topics (via ros_gz_bridge):

| ROS Topic | Type | Content |
|---|---|---|
| `/head_camera/image_raw` | sensor_msgs/Image | RGB image |
| `/head_camera/depth/image_raw` | sensor_msgs/Image (32FC1) | Depth in metres |
| `/head_camera/points` | sensor_msgs/PointCloud2 | 3D point cloud |
| `/head_camera/camera_info` | sensor_msgs/CameraInfo | Intrinsics |

**Coordinate frame notes:**  
Gazebo generates the PointCloud2 with `x = depth` along the sensor's `+X` axis. `camera_link` has `+X = forward`, which matches this convention, so the point cloud is correctly placed in front of the robot. `camera_optical_frame` (`+Z = forward`) is still published in TF via the `camera_to_optical` fixed joint for use with standard ROS vision pipelines.

---

## ROS ↔ Gazebo Bridge

Defined in `config/bridge.yaml`. The `ros_gz_bridge` node translates between `gz.msgs` (Gazebo) and `sensor_msgs` / `rosgraph_msgs` (ROS).

| ROS Topic | Direction | Purpose |
|---|---|---|
| `/clock` | GZ → ROS | Sim time for `use_sim_time:=true` |
| `/head_camera/image_raw` | GZ → ROS | RGB camera |
| `/head_camera/camera_info` | GZ → ROS | Camera intrinsics |
| `/head_camera/depth/image_raw` | GZ → ROS | Depth image |
| `/head_camera/points` | GZ → ROS | Point cloud |
| `/base_lidar/scan` | GZ → ROS | Base lidar scan |
| `/spine_lidar/scan` | GZ → ROS | Spine lidar scan |

---

## TF Tree

```
odom
└── base_footprint          ← published by diff_drive_controller
    └── base_link           ← static (base_footprint_joint)
        ├── left_wheel_link
        ├── right_wheel_link
        ├── caster_link
        └── torso_column_link   ← static (torso_column_fixed)
            └── torso_platform_link  ← dynamic (torso_z_joint)
                ├── left arm chain...
                ├── right arm chain...
                └── neck_pan_link   ← dynamic (neck_horizontal)
                    └── head_link   ← dynamic (neck_vertical)
                        └── camera_link  ← static (head_to_camera)
                            └── camera_optical_frame  ← static (camera_to_optical)
```

Static transforms for `head_link → camera_link` and `camera_link → camera_optical_frame` are published by both `robot_state_publisher` (once on `/tf_static`) and dedicated `static_transform_publisher` nodes (re-broadcast at 10 Hz). The redundant publishers exist because zenoh transport occasionally drops the one-shot RSP broadcast, causing intermittent "Could not transform" errors in RViz.

---

## Common Commands

```bash
# Drive the robot
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Set torso height (0.0 – 0.39 m)
ros2 topic pub --once /torso_position_controller/commands \
  std_msgs/msg/Float64MultiArray "{data: [0.20]}"

# Move neck
ros2 topic pub --once /joint_trajectory_controller/joint_trajectory \
  trajectory_msgs/msg/JointTrajectory \
  "{joint_names: [neck_horizontal], points: [{positions: [0.5], time_from_start: {sec: 1}}]}"

# Check all joint positions
ros2 topic echo /joint_states --once

# Check lidar is publishing
ros2 topic hz /base_lidar/scan

# Check depth camera
ros2 topic hz /head_camera/depth/image_raw
ros2 topic echo /head_camera/depth/image_raw --field header --once
```

---

## Known Behaviours and Quirks

**Torso effort interface:** The torso uses `effort` command interface rather than `position` because `gz_ros2_control`'s position interface implements velocity-tracking internally and cannot lift a vertical prismatic joint against gravity (upstream issue [#192](https://github.com/ros-controls/gz_ros2_control/issues/192)).

**Lidar TF via composed poses:** The lidar sensor definitions are placed on `base_footprint` in the Gazebo block rather than their own URDF links. This is required because sdformat's URDF→SDF converter lumps fixed-jointed child links into the parent, which silently drops any sensor definitions attached to those links. The workaround uses pre-computed world-space poses within the `base_footprint` sensor block, while keeping the URDF joints intact for TF.

**Camera frame convention:** `gz_frame_id = camera_link` rather than `camera_optical_frame`. Gazebo generates the PointCloud2 with `x = depth` in the sensor's body frame (not the ROS optical convention of `z = depth`). `camera_link` has `+X = forward`, which matches. When integrating with vision pipelines that expect optical convention, transform into `camera_optical_frame` using the static TF that is already in the tree.

**base_footprint as URDF root:** `base_link` is a child of `base_footprint` via a static joint. The diff_drive controller must use `base_frame_id: base_footprint` to avoid giving `base_link` two parents in the TF tree (one from `odom` via diff_drive, and one from `base_footprint` via RSP).

---

## Dependencies Summary

| Package | Purpose |
|---|---|
| `ros_gz_sim` | Gazebo Harmonic ROS 2 integration |
| `ros_gz_bridge` | Topic bridge between Gazebo and ROS |
| `gz_ros2_control` | `ros2_control` hardware plugin for Gazebo |
| `diff_drive_controller` | Differential drive base |
| `joint_trajectory_controller` | Arm and neck position control |
| `effort_controllers` | Torso force control |
| `joint_state_broadcaster` | Joint state publishing |
| `robot_state_publisher` | TF from URDF |
| `xacro` | URDF macro processing |
| `topic_tools` | Lidar relay in nav launch |
