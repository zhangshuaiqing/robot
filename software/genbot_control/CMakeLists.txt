cmake_minimum_required(VERSION 3.8)
project(genbot_control)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)

install(PROGRAMS
  genbot_control/ackermann_steering_node.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  genbot_control
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
