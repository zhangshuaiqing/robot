#!/usr/bin/env python3
"""
gazebo.launch.py — 在 Gazebo Harmonic 中启动 GenBot

用法:
  ros2 launch genbot_description gazebo.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            ExecuteProcess)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_dir = get_package_share_directory('genbot_description')
    urdf_path = os.path.join(pkg_dir, 'urdf', 'genbot.urdf.xacro')
    world_path = os.path.join(pkg_dir, 'worlds', 'genbot.world')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    world = LaunchConfiguration('world', default=world_path)

    robot_desc = Command(['xacro ', urdf_path])

    # 1. 启动 gz-sim (Gazebo Harmonic)
    # gz-sim 的 ros_gz_sim launch 文件
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('ros_gz_sim'),
                         'launch', 'gz_sim.launch.py')
        ]),
        launch_arguments={
            'gz_args': [' -r -v 4 ', world],
            'on_exit_shutdown': 'true',
        }.items()
    )

    # 2. Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': ParameterValue(robot_desc, value_type=str),
        }],
    )

    # 3. 生成机器人在Gazebo中
    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'genbot',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1',
        ],
        output='screen',
    )

    # 4. ros_gz_bridge 桥接 ROS2 ↔ Gazebo 话题
    # 将 Gazebo 的 /odom, /scan, /imu/data_raw 等桥接到 ROS2
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # 差速驱动 → ROS2
            '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            # LiDAR → ROS2
            '/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            # 相机
            '/camera/color/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            '/camera/color/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
            '/camera/depth/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            # IMU
            '/imu/data_raw@sensor_msgs/msg/Imu@gz.msgs.IMU',
            # TF
            '/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V',
        ],
        remappings=[
            ('/camera/color/image_raw', '/camera/image_raw'),
            ('/camera/color/camera_info', '/camera/camera_info'),
        ],
        output='screen',
    )

    # 5. rqt或键盘控制（可选）
    # 用 ros2 run teleop_twist_keyboard teleop_twist_keyboard 手动控制

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('world', default_value=world_path),
        gazebo,
        robot_state_publisher,
        spawn,
        bridge,
    ])
