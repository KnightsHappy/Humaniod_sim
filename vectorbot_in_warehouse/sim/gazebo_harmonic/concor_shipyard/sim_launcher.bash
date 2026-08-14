# Export the gazebo resources required
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/models

# Generate shipyard_world per configs and latest assets
python3 shipyard_world_generator.py

# Run the world file
gz sim shipyard_generated.sdf & # -> the & in the end puts the command in the background and then moves the execution to the next line, instead of getting stuck at this line.

# Run the Gazebo to ROS bridge
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:=bridge_config.yaml