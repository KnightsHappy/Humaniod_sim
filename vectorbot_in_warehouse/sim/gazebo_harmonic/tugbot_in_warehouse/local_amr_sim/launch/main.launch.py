import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('local_amr_sim') 
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    launch_rviz = LaunchConfiguration('launch_rviz', default='false')

    # --- DEFINE LOCAL PATHS ---
    local_worlds_path = os.path.join(pkg_share, 'worlds')
    local_models_path = os.path.join(pkg_share, 'models')
    
    world_file_path = os.path.join(local_worlds_path, 'tugbot_warehouse.sdf')
    model_sdf_path = os.path.join(local_models_path, 'tugbot', 'model.sdf')
    bridge_config_path = os.path.join(pkg_share, 'config', 'ros_gz_bridge.yaml')
    rviz_config_path = os.path.join(pkg_share, 'config', 'rviz.rviz')

    # --- SET ENVIRONMENT VARIABLES FOR GAZEBO HARMONIC ---
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[local_worlds_path, ':', local_models_path]
    )

    # Launch Gazebo
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': f'-r {world_file_path}'}.items(),
    )

    # --- ROBOT STATE PUBLISHER ---
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': open(model_sdf_path, 'r').read()
        }]
    )

    # --- PERFORMANCE OPTIMIZED ROS 2 GZ BRIDGE ---
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'use_sim_time': use_sim_time,
            'lazy': True,
            'config_file': bridge_config_path
        }],
        output='screen'
    )

    # --- STATIC TRANSFORM PUBLISHERS (THE FIX) ---
    # This node maps the Gazebo 3D PointCloud frame string directly onto your physical robot tree link
    static_tf_3d_lidar = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_3d_lidar',
        arguments=['0', '0', '0', '0', '0', '0', 'scan_omni', 'tugbot/scan_omni/scan_omni'],
        parameters=[{
            'use_sim_time': use_sim_time,
            # Force standard desktop logging syntax for ROS 2 Jazzy
        }]
    )

    # This node maps the Gazebo 2D Lidar frame string onto your physical robot tree link
    static_tf_2d_lidar = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_2d_lidar',
        arguments=['0', '0', '0', '0', '0', '0', 'scan_omni', 'tugbot/scan_omni/scan_omni_2d'],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(launch_rviz) # Node spins up only if launch_rviz is set to true
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('launch_rviz', default_value='false', description='Launch RViz2 tool visualization concurrently'),
        set_gz_resource_path, 
        gz_sim,
        robot_state_publisher,
        bridge,
        static_tf_3d_lidar,
        static_tf_2d_lidar
    ])