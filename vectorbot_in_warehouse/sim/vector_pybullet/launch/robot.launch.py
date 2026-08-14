from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='vector_pybullet',
            executable='robot.py',
            name='vector_pybullet',
            output='screen'
        )
    ])

