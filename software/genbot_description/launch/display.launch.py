#!/usr/bin/env python3
"""
display.launch.py — 在RViz中查看GenBot模型

用法:
  ros2 launch genbot_description display.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.conditions import IfCondition


def generate_launch_description():
    pkg_dir = get_package_share_directory('genbot_description')
    urdf_path = os.path.join(pkg_dir, 'urdf', 'genbot.urdf.xacro')

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    gui = LaunchConfiguration('gui', default='true')
    rviz = LaunchConfiguration('rviz', default='true')

    robot_desc = Command(['xacro ', urdf_path])

    # robot_state_publisher: 从robot_description发布所有TF
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': ParameterValue(robot_desc, value_type=str),
        }],
    )

    # joint_state_publisher_gui: 发布可动joint的state + GUI滑条
    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        condition=IfCondition(gui),
    )

    # 静态TF: base_footprint -> base_link
    # 由于joint_state_publisher_gui不发布fixed joint的state，
    # robot_state_publisher无法自动发布base_footprint的TF。
    # 这里手动发布base_footprint在底部的静态变换。
    clearance = 0.050
    chassis_height = 0.080
    base_link_z = clearance + chassis_height / 2
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'base_footprint', 'base_link'],
    )

    rviz_config = os.path.join(pkg_dir, 'rviz', 'genbot.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        condition=IfCondition(rviz),
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        static_tf,
        robot_state_publisher,
        joint_state_publisher_gui,
        rviz_node,
    ])
