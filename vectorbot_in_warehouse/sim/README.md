## Pybullet Documentation (to be revamped): [Notion](https://www.notion.so/Robot-Control-Using-PyBullet-Simulator-1d767df95395809dbce2ec8e78333352)

## System Info
- Ubuntu 24.04
- ROS2 Jazzy
- Gazebo Harmonic

## Gazebo Documentation
- Gazebo simulation files are in gazebo_harmonic folder (ROS2 Jazzy and Ubuntu 24.04 compatibility)
- *Detailed beginner friendly Google Gemini chat for creating and setting up a custom Gazebo world, robot with sensors and linking with ROS2 Jazzy*: https://www.notion.so/How-to-Create-a-Custom-World-Robot-Model-and-Sensors-for-robot-in-Gazebo-Harmonic-ROS2-Jazzy-Ubunt-2e467df953958027a50dee25141aff02
- Before executing, please make sure ROS2 Jazzy (standard which includes gazebo) is installed on your system.
- Then execute the following to install required packages via the Ubuntu terminal: `sudo apt update && sudo apt install -y ros-jazzy-ros-gz && sudo apt install -y ros-jazzy-teleop-twist-keyboard`

## Concor Shipyard Project
- Install the required python packages by executing the following commands on the Ubuntu terminal: `pip install Pillow easyocr opencv-python --break-system-packages`
- For the concor_shipyard project, when all is done, in the terminal, navigate to the *gazebo_harmonic/concor_shipyard* folder and then execute `ros2 launch main.launch.py` to generate the world and launch everything (including RViz)

## Tugbot in Warehouse
- Pre-requisites: Gazebo Harmonic, ROS2 Jazzy, Ubuntu 24.04 (tested on regular computer installation, not VM or WSL2)
- Open a terminal in Ubuntu and inside this repo folder, navigate to the *gazebo_harmonic/tugbot_in_warehouse* folder
- Build the local_amr_sim ros2 package by executing `colcon build`
- Once done, execute `source install/setup.bash` and then execute `ros2 launch local_amr_sim main.launch.py`