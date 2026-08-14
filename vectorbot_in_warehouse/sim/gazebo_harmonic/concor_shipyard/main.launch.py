import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess, AppendEnvironmentVariable, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    base_path = os.path.abspath('.') # equivalent to executing $(pwd) in a terminal
    models_path = os.path.join(base_path, 'models')
    world_gen_script = os.path.join(base_path, 'shipyard_world_generator.py')
    world_file = os.path.join(base_path, 'shipyard_generated.sdf')
    bridge_config = os.path.join(base_path, 'bridge_config.yaml')
    rviz_config = os.path.join(base_path, 'shipyard.rviz')
    verifier_script = os.path.join(base_path, 'shipyard_verifier.py')

    # --- 1. Append to GZ_SIM_RESOURCE_PATH ---
    # This acts like: export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models
    append_gz_resource_path = AppendEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=models_path
    )

    # Execute the world generator script
    generate_world = ExecuteProcess(
        cmd=['python3', world_gen_script],
        output='screen'
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ]),
        launch_arguments={'gz_args': f'-r {world_file}'}.items()
    )

    gz_ros_bridge = Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            parameters=[{"config_file": bridge_config}],
            output='screen'
        )
    
    tf_lidar = Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0.3', '0', '2.2', '0', '0', '0', 'robot/base_link', 'robot/lidar_link/gpu_lidar'],
        )
    
    tf_camera_right = Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0.3', '-0.1', '1.8', '-1.57', '0', '1.57', 'robot/base_link', 'robot/camera_link/camera_right']
        )
    
    rviz = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            output='screen'
        )
    
    # 7. Verifier Node (Running as a raw python process for terminal printing)
    verifier = ExecuteProcess(
        cmd=['python3', verifier_script],
        output='screen'
    )
    
    # This waits for 'generate_world' to exit (finish writing the file) 
    # then launches Gazebo, the Bridge, and RViz.
    delayed_start = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=generate_world,
            on_exit=[gz_sim, gz_ros_bridge, tf_lidar, tf_camera_right, rviz]
        )
    )
    
    return LaunchDescription([
        append_gz_resource_path,
        generate_world,
        delayed_start
    ])