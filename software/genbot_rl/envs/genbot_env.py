"""
GenBot MuJoCo RL 导航环境（Gymnasium 接口）

阿克曼转向底盘，PPO/SAC 训练自主导航。
"""

import os
import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import mujoco

# 阿克曼几何：计算左右轮转向角
# 左转时 steering_angle > 0
def ackermann_angles(steer_cmd, wheel_base, wheel_track, max_steer):
    """将归一化转向命令[-1,1]转为左右轮实际转角"""
    angle = steer_cmd * max_steer
    if abs(angle) < 0.001:
        return 0.0, 0.0
    # 阿克曼几何
    R = wheel_base / math.tan(abs(angle))
    inner = math.atan2(wheel_base, R - wheel_track / 2.0)
    outer = math.atan2(wheel_base, R + wheel_track / 2.0)
    if angle > 0:  # 左转
        return inner, outer
    else:          # 右转
        return -outer, -inner


class GenBotNavEnv(gym.Env):
    """GenBot 阿克曼导航环境"""

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 50}

    def __init__(self, render_mode=None, max_steps=500):
        super().__init__()

        self.render_mode = render_mode
        self.max_steps = max_steps
        self.step_count = 0

        # 机器人参数
        self.wheel_base = 0.30
        self.wheel_track = 0.24
        self.max_steer = 0.6       # 最大转向角（弧度）
        self.max_speed = 5.0        # 后轮最大角速度 (rad/s)
        self.wheel_radius = 0.05

        # 加载 MuJoCo 模型（相对路径，相对于本文件位置）
        xml_path = os.path.join(
            os.path.dirname(__file__), "..", "xml", "genbot_ackermann.xml"
        )
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)

        # 观察空间: LiDAR(16) + 目标相对位置(2) + 目标距离(1) + 速度(1) = 20维
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(20,), dtype=np.float32
        )

        # 动作空间: [油门(-1~1), 转向(-1~1)]
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(2,), dtype=np.float32
        )

        # 渲染
        if self.render_mode == "human":
            self.viewer = mujoco.viewer.launch(self.model, self.data)
        else:
            self.viewer = None

        # 自动重置
        self.reset()

    def _get_obs(self):
        """获取观察值"""
        # LiDAR：用 MuJoCo mj_ray 手动做 16 束射线检测
        lidar = np.zeros(16, dtype=np.float32)
        chassis_pos = self.data.body("chassis").xpos
        chassis_mat = self.data.body("chassis").xmat.reshape(3, 3)
        origin = chassis_pos + chassis_mat @ np.array([0, 0, 0.05])

        for i in range(16):
            angle = 2 * math.pi * i / 16
            # 水平方向射线
            direction = chassis_mat @ np.array([math.cos(angle), math.sin(angle), 0])
            direction = direction / np.linalg.norm(direction)

            dist = mujoco.mj_ray(
                self.model, self.data, origin, direction,
                None, 1, -1
            )[0]
            lidar[i] = np.clip(dist if dist > 0 else 3.0, 0.0, 3.0)

        # 获取机器人位置和朝向
        chassis_pos = self.data.body("chassis").xpos[:2]
        chassis_rot = self.data.body("chassis").xmat.reshape(3, 3)
        yaw = math.atan2(chassis_rot[1, 0], chassis_rot[0, 0])

        # 目标位置（世界坐标）
        target_pos = self.data.body("target").xpos[:2]

        # 目标相对位置（机器人坐标系）
        dx = target_pos[0] - chassis_pos[0]
        dy = target_pos[1] - chassis_pos[1]
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        local_dx = dx * cos_yaw + dy * sin_yaw
        local_dy = -dx * sin_yaw + dy * cos_yaw
        target_dist = math.sqrt(dx**2 + dy**2)

        # 速度（由 qvel 计算，linear velocity from freejoint）
        speed = math.sqrt(
            self.data.qvel[0]**2 + self.data.qvel[1]**2
        )

        obs = np.concatenate([
            lidar.astype(np.float32),        # 16
            np.array([local_dx, local_dy], dtype=np.float32),  # 2
            np.array([target_dist], dtype=np.float32),          # 1
            np.array([speed], dtype=np.float32),                # 1
        ])
        return obs

    def _get_reward(self, obs, collision, lidar_min):
        """计算奖励"""
        target_dist = obs[18]

        reward = 0.0

        # 1. 到达目标
        if target_dist < 0.3:
            reward += 100.0
            return reward, True, True  # reward, terminated, truncated

        # 2. 靠近目标奖励（势能 shaping）
        if hasattr(self, '_prev_dist'):
            delta = self._prev_dist - target_dist
            reward += delta * 5.0
        self._prev_dist = target_dist

        # 3. 碰撞惩罚（基于物理接触，非lidar）
        if collision:
            reward -= 50.0
            return reward, True, False

        # 近障碍警告（基于lidar，但需要lidar可信）
        if lidar_min > 0.01 and lidar_min < 0.3:
            reward -= 0.5

        # 4. 每步微小惩罚
        reward -= 0.01

        return reward, False, False

    def _apply_action(self, action):
        """将动作[油门, 转向]应用到 MuJoCo 执行器"""
        throttle = float(np.clip(action[0], -1.0, 1.0))
        steer = float(np.clip(action[1], -1.0, 1.0))

        # 后轮速度：油门 * 最大角速度
        wheel_speed = throttle * self.max_speed
        self.data.ctrl[0] = wheel_speed   # rear_left_motor
        self.data.ctrl[1] = wheel_speed   # rear_right_motor

        # 阿克曼转向角
        left_angle, right_angle = ackermann_angles(
            steer, self.wheel_base, self.wheel_track, self.max_steer
        )
        self.data.ctrl[2] = left_angle    # front_left_steer_act
        self.data.ctrl[3] = right_angle   # front_right_steer_act

    def reset(self, seed=None, options=None):
        """重置环境：随机起点和目标"""
        super().reset(seed=seed)

        # 随机初始化机器人位置
        angle = self.np_random.uniform(-math.pi, math.pi)
        x = self.np_random.uniform(-1.5, 1.5)
        y = self.np_random.uniform(-1.5, 1.5)
        qpos = np.array([x, y, 0, math.cos(angle/2), 0, 0, math.sin(angle/2)])

        self.data.qpos[:7] = qpos
        mujoco.mj_forward(self.model, self.data)

        # 随机目标位置（在场地范围内，不跟起点太近）
        while True:
            tx = self.np_random.uniform(-2.0, 2.0)
            ty = self.np_random.uniform(-2.0, 2.0)
            if math.sqrt((tx-x)**2 + (ty-y)**2) > 1.0:
                break

        self.data.body("target").xpos[:2] = [tx, ty]
        mujoco.mj_forward(self.model, self.data)

        self.step_count = 0
        obs = self._get_obs()
        self._prev_dist = obs[18]

        return obs, {}

    def step(self, action):
        """执行一步动作"""
        self._apply_action(action)

        # 物理仿真步进
        for _ in range(10):  # 每个动作执行10个物理步（0.05s总时长）
            mujoco.mj_step(self.model, self.data)

        self.step_count += 1

        # 碰撞检测
        collision = False
        for i in range(self.data.ncon):
            contact = self.data.contact[i]
            g1 = self.model.geom(contact.geom1).name
            g2 = self.model.geom(contact.geom2).name
            # 轮子与地面的接触不算碰撞
            if "wheel" in g1 or "wheel" in g2:
                continue
            if "floor" in g1 or "floor" in g2:
                continue
            if contact.dist < 0:
                collision = True
                break

        obs = self._get_obs()
        lidar_min = np.min(obs[:16])
        reward, terminated, truncated = self._get_reward(obs, collision, lidar_min)

        # 超时截断
        if self.step_count >= self.max_steps:
            truncated = True
            reward -= 50.0

        done = terminated or truncated

        if self.render_mode == "human" and self.viewer is not None:
            self.viewer.sync()

        return obs, reward, terminated, truncated, {}

    def render(self):
        if self.render_mode == "rgb_array":
            return mujoco.renderer.render(
                self.model, self.data,
                camera="fixed",
                width=640, height=480
            )

    def close(self):
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None
