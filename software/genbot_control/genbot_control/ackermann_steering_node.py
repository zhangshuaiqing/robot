#!/usr/bin/env python3
"""
ackermann_steering_node.py

将 /cmd_vel (Twist) 中的 angular.z 转换为阿克曼转向角，
发布到 /cmd_steer_left 和 /cmd_steer_right (Float64)。

阿克曼几何:
  tan(steer_left)  = wheel_base / (R + track/2)
  tan(steer_right) = wheel_base / (R - track/2)
  其中 R = wheel_base / tan(steering_angle)
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64


class AckermannSteeringNode(Node):
    def __init__(self):
        super().__init__('ackermann_steering_node')

        self.declare_parameter('wheel_base', 0.300)
        self.declare_parameter('wheel_track', 0.240)
        self.declare_parameter('max_steering_angle', 0.6)

        self.wheel_base = self.get_parameter('wheel_base').value
        self.wheel_track = self.get_parameter('wheel_track').value
        self.max_steer = self.get_parameter('max_steering_angle').value

        self.steer_left_pub = self.create_publisher(Float64, '/cmd_steer_left', 10)
        self.steer_right_pub = self.create_publisher(Float64, '/cmd_steer_right', 10)

        self.sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)

        self.get_logger().info(
            f'Ackermann node started: base={self.wheel_base}m, track={self.wheel_track}m'
        )

    def cmd_callback(self, msg: Twist):
        v = msg.linear.x
        omega = msg.angular.z

        # 阿克曼转向：速度为0时不能转向，但需要处理 teleop 的纯旋转命令
        # 此时用一个最小速度来产生转向
        if abs(v) < 0.01:
            if abs(omega) > 0.01:
                # 纯旋转命令：用小速度配合转角来实现
                v = 0.1 * (1.0 if omega > 0 else -1.0)
            else:
                # 完全停止
                steer_left = Float64()
                steer_right = Float64()
                steer_left.data = 0.0
                steer_right.data = 0.0
                self.steer_left_pub.publish(steer_left)
                self.steer_right_pub.publish(steer_right)
                return

        # 转弯半径 R = v / omega
        R = v / omega if abs(omega) > 0.001 else float('inf')

        # 中心转向角（带符号，正=左转，负=右转）
        if math.isfinite(R):
            steering_angle = math.atan(self.wheel_base / abs(R))
            steering_angle = math.copysign(steering_angle, omega)  # 符号跟随omega
        else:
            steering_angle = 0.0

        steering_angle = max(-self.max_steer, min(self.max_steer, steering_angle))

        # 阿克曼几何：左右轮转角不同
        # 注意：左转时 steering_angle > 0，右转时 < 0
        if abs(steering_angle) > 0.001:
            abs_angle = abs(steering_angle)
            R_turn = self.wheel_base / math.tan(abs_angle)
            inner_angle = math.atan2(self.wheel_base, R_turn - self.wheel_track / 2.0)
            outer_angle = math.atan2(self.wheel_base, R_turn + self.wheel_track / 2.0)
            if steering_angle > 0:
                # 左转：左轮是内轮（转角大），右轮是外轮（转角小）
                left_angle = inner_angle
                right_angle = outer_angle
            else:
                # 右转：右轮是内轮（转角大），左轮是外轮（转角小）
                left_angle = -outer_angle
                right_angle = -inner_angle
        else:
            left_angle = 0.0
            right_angle = 0.0

        steer_left = Float64()
        steer_right = Float64()
        steer_left.data = left_angle
        steer_right.data = right_angle

        self.steer_left_pub.publish(steer_left)
        self.steer_right_pub.publish(steer_right)

        self.get_logger().info(
            f'v={v:.2f} ω={omega:.2f} → steer_L={left_angle:.3f} steer_R={right_angle:.3f}',
            throttle_duration_sec=0.5
        )


def main():
    rclpy.init()
    node = AckermannSteeringNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
