"""
Vector Gazebo simulation launcher (ROS 2 Jazzy + Gazebo Harmonic).

Topic flow:
  Standalone:
      teleop publishes /cmd_vel (Twist)
        ─→ twist_to_stamped (C++ node) ─→ /base_controller/cmd_vel (TwistStamped)

  With OS:
      OS pipeline publishes /cmd_vel_final (Twist)
        ─→ twist_to_stamped (C++ node) ─→ /base_controller/cmd_vel (TwistStamped)
"""
import os
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def resolve_active_joints():
    """The active joints the JTC controls in simulation."""
    return [
        "left_shoulder_1",
        "right_shoulder_1",
        "left_elbow_1",
        "left_elbow_2",
        "right_elbow_1",
        "right_elbow_2",
    ]

def write_jtc_override(joints, out_path):
    payload = {"joint_trajectory_controller": {"ros__parameters": {"joints": joints}}}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        yaml.dump(payload, f)


def find_os_launch_file(os_ws: str):
    home = os.path.expanduser("~")
    candidates = []
    if os_ws:
        ws = os.path.expanduser(os_ws)
        candidates.append(os.path.join(ws, "install", "vector_hardware_controllers",
                                       "share", "vector_hardware_controllers",
                                       "launch", "main.launch.py"))
    try:
        pkg = get_package_share_directory("vector_hardware_controllers")
        candidates.append(os.path.join(pkg, "launch", "main.launch.py"))
    except Exception:
        pass
    for guess in ["vector_os", "ros2_ws", "vector_ws"]:
        candidates.append(os.path.join(home, guess, "install", "vector_hardware_controllers",
                                       "share", "vector_hardware_controllers",
                                       "launch", "main.launch.py"))
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def make_bridge(input_topic: str, name: str):
    """Spawn the C++ twist_to_stamped bridge with custom topic remap."""
    return Node(
        package="vector_gazebo_sim",
        executable="twist_to_stamped",
        name=name,
        parameters=[{
            "use_sim_time":  True,
            "input_topic":   input_topic,
            "output_topic":  "/base_controller/cmd_vel",
            "frame_id":      "base_link",
        }],
        output="screen",
    )


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory("vector_description")
    gazebo_pkg_share = get_package_share_directory("vector_gazebo_sim")

    headless   = LaunchConfiguration("headless").perform(context).lower() == "true"
    launch_os  = LaunchConfiguration("launch_os").perform(context).lower() == "true"
    world_file = LaunchConfiguration("world").perform(context)
    os_ws      = LaunchConfiguration("os_ws").perform(context)

    # JTC joint override file (read by URDF gz_ros2_control plugin)
    jtc_override_path = os.path.join(gazebo_pkg_share, "config", "jtc_joints_override.yaml")
    write_jtc_override(resolve_active_joints(), jtc_override_path)

    # Path to ros2_controllers config — passed to xacro to override the hardcoded path in URDF
    # The URDF's gz_ros2_control plugin needs this path to load controller configurations
    ros2_controllers_config = os.path.join(gazebo_pkg_share, "config", "gz_ros2_control_config.yaml")

    # Use vector.xacro which has all the proper mesh files for the humanoid robot
    # industrial_robot.urdf.xacro only includes primitive geometry (boxes, cylinders) with no real meshes
    urdf_xacro = os.path.join(pkg_share, "urdf", "vector.xacro")
    # Pass the config file path as a xacro argument so the URDF can use it dynamically
    # Construct as a single shell command string for reliable argument passing
    robot_description_content = ParameterValue(
        Command(f"xacro {urdf_xacro} ros2_controllers_config:={ros2_controllers_config}"),
        value_type=str,
    )
    robot_description_params = {
        "robot_description": robot_description_content,
        "use_sim_time": True,
    }

    # ── Gazebo Harmonic ──────────────────────────────────────────────
    world_path = os.path.join(gazebo_pkg_share, "worlds", world_file)
    gz_args = f"-v 4 -r {world_path}"
    if headless:
        gz_args = f"-v 4 -r -s --headless-rendering {world_path}"
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ros_gz_sim"),
                                  "launch", "gz_sim.launch.py"])
        ),
        launch_arguments={"gz_args": gz_args, "gz_version": "8"}.items(),
    )

    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description_params],
        output="screen",
    )

    spawn_robot = ExecuteProcess(
        cmd=[
            '/opt/ros/jazzy/lib/ros_gz_sim/create',
            '-name', 'vector_robot',
            '-topic', '/robot_description',
            '-z', '0.170',
            '-Y', '-1.5708',   # Rotate -90° so URDF Y+ points forward (drive wheels become left/right)
        ],
        additional_env={'ROS_DOMAIN_ID': os.environ.get('ROS_DOMAIN_ID', '0')},
        output='screen',
    )

    bridge_config = os.path.join(gazebo_pkg_share, "config", "bridge.yaml")
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[{"config_file": bridge_config, "use_sim_time": True}],
        output="screen",
    )

    # ── Spawners (delayed for plugin to come up) ──────────────────────
    def make_spawner(name, extra_args=None):
        args = [name, "--controller-manager-timeout", "60"]
        if extra_args:
            args += extra_args
        return Node(
            package="controller_manager",
            executable="spawner",
            arguments=args,
            parameters=[{"use_sim_time": True}],
            output="screen",
        )

    delayed_spawners = TimerAction(
        period=5.0,
        actions=[
            make_spawner("joint_state_broadcaster"),
            make_spawner("base_controller"),
            make_spawner("joint_trajectory_controller", ["--param-file", jtc_override_path]),
            make_spawner("torso_effort_controller"),
        ],
    )


    # ── Torso position PID (software loop, outputs effort) ────────────
    # Architecture (see src/torso_position_pid.cpp for full explanation):
    #   /torso_position_controller/commands  (Float64MultiArray, OS publishes)
    #     → torso_position_pid (this node)
    #     → /torso_effort_controller/commands
    #     → effort_controllers/JointGroupEffortController
    #     → torso_z_joint effort interface in Gazebo
    #
    # Gains derived from physics (m=31.62kg, ωn=4 rad/s, ζ=1.0):
    #   kp = m·ωn² = 506.0      kd = 2·ζ·m·ωn = 253.0
    # gravity_feedforward_n = m·g = 310.2 N (cancels weight)
    # ki = 0 (FF holds steady state, I term causes windup on vertical joints)
    #
    # Live tuning: ros2 param set /torso_position_pid <param> <value>
    torso_pid = Node(
        package="vector_gazebo_sim",
        executable="torso_position_pid",
        name="torso_position_pid",
        parameters=[{
            "use_sim_time":            True,
            "joint_name":              "torso_joint",
            "kp":                      506.0,
            "ki":                      0.0,
            "kd":                      253.0,
            "gravity_feedforward_n":   310.2,
            "max_effort":              2000.0,
            "min_effort":             -2000.0,
            "min_position":            0.0,
            "max_position":            0.5,
            "integral_clamp":          100.0,
            "setpoint_slew_m_per_s":   0.15,
            "deadband_m":              0.001,
        }],
        output="screen",
    )

    # ── Torso arm-collision safety guard ─────────────────────────────
    # Intercepts torso commands BEFORE they reach the PID. If arms are
    # in an unsafe pose (hanging down), refuses to lower the torso below
    # safe_min_torso_z. Republishes safe commands on .../commands_safe
    # which torso_position_pid actually subscribes to.
    #
    # Live tunable: ros2 param set /torso_safety_guard <param> <value>
    torso_safety = Node(
        package="vector_gazebo_sim",
        executable="torso_safety_guard",
        name="torso_safety_guard",
        parameters=[{
            "use_sim_time":                   True,
            "safe_min_torso_z":               0.0,
            "shoulder_safe_threshold_rad":    0.6,    # arm is safe if |shoulder_1| > 0.6 rad
            "elbow_safe_threshold_rad":       0.9,    # ... or if |elbow_2| > 0.9 rad
            "max_torso_z":                    0.5,
            "verbose":                        True,
        }],
        output="screen",
    )

    # ── cmd_vel routing via C++ bridge ────────────────────────────────
    # Static TF for the fixed camera joints.
    # robot_state_publisher sends these on /tf_static (latched, once).
    # Over zenoh that one-shot broadcast is occasionally missed, causing
    # "Could not transform from camera_optical_frame to base_link" errors
    # in RViz.  static_transform_publisher re-broadcasts at 10 Hz so the
    # transform is always in the TF buffer regardless of transport drops.
    # Redundant: camera_1 is now defined inside URDF as a fixed joint/link
    # camera_link_tf = Node(
    #     package="tf2_ros",
    #     executable="static_transform_publisher",
    #     name="camera_link_static_tf",
    #     arguments=["-0.0702", "0.0605", "0.184373", "0", "0", "0",
    #                "torso_link", "camera_1"],
    #     parameters=[{"use_sim_time": True}],
    #     output="log",
    # )
    camera_optical_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="camera_optical_static_tf",
        arguments=["0", "0", "0", "-1.5708", "0", "-1.5708",
                   "camera_1", "camera_optical_frame"],
        parameters=[{"use_sim_time": True}],
        output="log",
    )

    # ── Torso teleop bridge (Q/E keys → torso position) ────────────────
    # The Gazebo Teleop plugin publishes linear.z on /cmd_vel when Q/E are
    # pressed.  The diff_drive_controller ignores linear.z.  This node
    # converts linear.z into incremental position commands for the torso.
    torso_teleop = Node(
        package="vector_gazebo_sim",
        executable="torso_teleop_bridge",
        name="torso_teleop_bridge",
        parameters=[{
            "use_sim_time":  True,
            "rate_m_per_s":  0.15,
            "min_position":  0.0,
            "max_position":  0.5,
            "update_hz":     20.0,
        }],
        output="screen",
    )

    # ── Livox Mid-360 LiDAR monitor ────────────────────────────────────
    # Subscribes to /livox_mid360/scan, /points, /imu and publishes
    # diagnostics JSON + periodic console logs with range/coverage/IMU stats.
    lidar_monitor = Node(
        package="vector_gazebo_sim",
        executable="lidar_monitor",
        name="lidar_monitor",
        parameters=[{
            "use_sim_time":       True,
            "log_rate_hz":        1.0,
            "warn_min_range_m":   0.3,
            "warn_no_data_sec":   3.0,
        }],
        output="screen",
    )

    # ── Joint torque feedback monitor ──────────────────────────────────
    # Reads effort field from /joint_states, publishes JSON on:
    #   /torque_monitor/joint_efforts   — per-joint effort/pos/vel data
    #   /torque_monitor/diagnostics     — summary stats, anomaly flags
    # Optionally logs CSV for offline analytics (enable_csv_log param).
    # Any external plugin can subscribe to these topics for real-time data.
    torque_monitor = Node(
        package="vector_gazebo_sim",
        executable="torque_monitor",
        name="torque_monitor",
        parameters=[{
            "use_sim_time":           True,
            "log_rate_hz":            2.0,
            "publish_rate_hz":        10.0,
            "enable_csv_log":         False,
            "csv_path":               "/tmp/vector_torque_log.csv",
            "warn_effort_threshold":  50.0,
        }],
        output="screen",
    )

    # Static TF for Livox Mid-360 (same reason as camera_link_tf above —
    # ensures the transform is always in the TF buffer over zenoh/DDS).
    # Parented to slider_1 (top of base column), offset to column center.
    # Redundant: livox_mid360_link is now defined inside URDF as a fixed joint/link
    # lidar_tf = Node(
    #     package="tf2_ros",
    #     executable="static_transform_publisher",
    #     name="livox_mid360_static_tf",
    #     arguments=["-0.083", "0.06", "0.94", "0", "0", "0",
    #                "base_link", "livox_mid360_link"],
    #     parameters=[{"use_sim_time": True}],
    #     output="log",
    # )

    nodes = [
        gz_sim, rsp, bridge, spawn_robot, delayed_spawners,
        torso_safety,
        torso_pid,
        torso_teleop,
        # camera_link_tf,
        camera_optical_tf,
        lidar_monitor,
        torque_monitor,
        # lidar_tf,
        make_bridge("/cmd_vel_final", "twist_bridge_final"),
    ]

    # Standalone teleop also publishes plain Twist on /cmd_vel — bridge it too
    if not launch_os:
        nodes.append(make_bridge("/cmd_vel", "twist_bridge_direct"))
        print("[vector_gazebo_sim] Standalone mode: /cmd_vel and /cmd_vel_final both bridged.")
    else:
        print("[vector_gazebo_sim] OS mode: only /cmd_vel_final is bridged (OS handles /cmd_vel).")

    # ── Optional embedded OS launch ──────────────────────────────────
    if launch_os:
        launch_path = find_os_launch_file(os_ws)
        if launch_path:
            print(f"[vector_gazebo_sim] Embedding OS launch: {launch_path}")
            os_launch = IncludeLaunchDescription(
                PythonLaunchDescriptionSource(launch_path),
                launch_arguments={"use_sim": "true"}.items(),
            )
            nodes.append(TimerAction(period=8.0, actions=[os_launch]))
        else:
            print(
                "\n[vector_gazebo_sim] ERROR: cannot locate vector_hardware_controllers.\n"
                "  Run with: launch_os:=true os_ws:=/home/ishaan/vector_os\n"
                "  Or source ~/vector_os/install/setup.bash before launching.\n"
            )

    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("world", default_value="warehouse.sdf"),
        DeclareLaunchArgument("headless", default_value="false"),
        DeclareLaunchArgument("launch_os", default_value="false"),
        DeclareLaunchArgument("os_ws", default_value=""),
        OpaqueFunction(function=launch_setup),
    ])
