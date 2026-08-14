from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='vector_pybullet',
            executable='warehouse_teleop.py',
            name='warehouse_teleop',
            output='screen'
        )  
        
    ])

