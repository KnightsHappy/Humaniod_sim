"""
Standalone test launch — spawns the robot in Gazebo and opens RViz so
you can verify joints and topics before involving the full OS.

ros2 launch vector_gazebo_sim test.launch.py
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("vector_gazebo_sim")
    sim_launch = os.path.join(pkg_share, "launch", "sim.launch.py")

    rviz_config = os.path.join(pkg_share, "rviz", "vector_sim.rviz")

    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(sim_launch)),
        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", rviz_config] if os.path.exists(rviz_config) else [],
            parameters=[{"use_sim_time": True}],
            output="log",
        ),
    ])
