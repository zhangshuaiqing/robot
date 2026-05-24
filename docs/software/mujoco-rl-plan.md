# MuJoCo RL 导航训练方案

> 目标：在 MuJoCo 仿真中训练 GenBot 阿克曼底盘自主导航模型
> 方法：深度强化学习（PPO/SAC）+ Gymnasium 环境封装

---

## 一、路线图

```
MuJoCo XML 模型                  Gymnasium 环境                SB3 训练
┌─────────────────┐      ┌─────────────────────┐      ┌──────────────────┐
│ 阿克曼底盘模型    │ ──→ │  obs: LiDAR + odom  │ ──→ │  PPO / SAC       │
│ 前轮转向关节      │      │  + 目标相对位置      │      │  训练导航策略      │
│ 后轮驱动关节      │      │  action: 油门+转角   │      │  → policy.zip    │
│ LiDAR传感器      │      │  reward: 到目标+避障  │      │                  │
└─────────────────┘      └─────────────────────┘      └──────────────────┘
```

## 二、环境搭建

### 2.1 安装依赖

```bash
cd <项目路径>/robot/software/genbot_rl
uv sync
```

这会安装：
- `mujoco>=3.0` — MuJoCo 物理引擎（官方 Python 绑定）
- `gymnasium>=1.0` — RL 环境标准接口
- `stable-baselines3>=2.0` — 强化学习算法库（PPO/SAC）
- `torch>=2.0` — 深度学习框架
- `numpy`, `matplotlib` — 数据处理和可视化

如果 uv sync 超时，可以分步安装：

```bash
cd <项目路径>/robot/software/genbot_rl
uv pip install mujoco
uv pip install gymnasium
uv pip install stable-baselines3
uv pip install matplotlib
```

验证安装：

```bash
cd <项目路径>/robot/software/genbot_rl
uv run python -c "import mujoco; print('MuJoCo', mujoco.__version__)"
uv run python -c "import gymnasium; print('Gymnasium', gymnasium.__version__)"
uv run python -c "from stable_baselines3 import PPO; print('SB3 OK')"
```

## 三、MuJoCo XML 模型

### 文件位置

`software/genbot_rl/xml/genbot_ackermann.xml`

### 模型结构

```
worldbody
├── light          # 光照
├── floor          # 地面（带摩擦参数）
│
├── chassis        # 底盘（box）
│   ├── front_left_steering    ← hinge 关节（绕Z轴，转向）
│   │   └── front_left_wheel   ← hinge 关节（绕Y轴，滚动）
│   ├── front_right_steering   ← hinge 关节（绕Z轴，转向）
│   │   └── front_right_wheel  ← hinge 关节（绕Y轴，滚动）
│   ├── rear_left_wheel        ← hinge 关节（绕Y轴，驱动）
│   └── rear_right_wheel       ← hinge 关节（绕Y轴，驱动）
│
├── lidar_site     # LiDAR 位置标记
└── target         # 目标点标记（训练时移动）
```

### 阿克曼转向的 MuJoCo 实现

MuJoCo 不提供阿克曼转向插件，需要手动实现：
- **动作空间**：`[speed, steer_angle]` — 油门和转向角
- **后轮**：通过 `velocity` motor 控制转速
- **前轮**：通过 `position` actuator 控制转向角（带符号：左转为正）
- **阿克曼解算**：在环境代码中用几何公式计算左右轮转角差

## 四、Gymnasium 环境

### 文件位置

`software/genbot_rl/envs/genbot_env.py`

### 观察空间

| 维度 | 内容 | 范围 | 说明 |
|------|------|------|------|
| 0-15 | LiDAR 扫描 | [0, 3.0] | 16束激光，检测障碍物距离 |
| 16-17 | 目标相对位置 | [-3, 3] | dx, dy（相对于机器人坐标系）|
| 18 | 目标距离 | [0, 5] | 归一化距离 |
| 19 | 当前线速度 | [-0.5, 0.5] | 机器人速度 |
| **20维** | **总计** | | |

### 动作空间

| 维度 | 内容 | 范围 | 说明 |
|------|------|------|------|
| 0 | 油门 | [-1, 1] | 正=前进，负=后退 |
| 1 | 转向角 | [-1, 1] | 归一化，乘 max_steer 得实际角度 |

### 奖励函数

```
总奖励 = r_goal + r_progress + r_safe + r_alive + r_done_penalty

r_goal = +100          # 到达目标
r_progress = Δdist * 5  # 靠近目标的正奖励
r_safe = -0.5 if 障碍物 < 0.3m else 0   # 碰撞惩罚（近障碍）
r_alive = -0.01        # 每步微小惩罚（鼓励尽快到达）
r_done_penalty = -50   # 碰撞/超时惩罚
```

### 终止条件

- ✅ 到达目标（距离 < 0.3m）
- ❌ 碰撞（LiDAR 检测 < 0.15m）
- ❌ 超时（超过 500 步）

## 五、训练脚本

### 文件位置

`software/genbot_rl/scripts/train.py`

### 训练流程

```python
from sb3 import PPO
from envs.genbot_env import GenBotEnv

# 创建环境
env = GenBotEnv(render=False)

# 初始化模型
model = PPO(
    "MlpPolicy",
    env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    verbose=1,
)

# 开始训练
model.learn(total_timesteps=1_000_000)

# 保存策略
model.save("models/nav_policy")
```

### 超参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 算法 | PPO | 稳定，适合连续控制 |
| 策略网络 | [256, 256] | 两层 MLP |
| 学习率 | 3e-4 |  |
| n_steps | 2048 | 每次更新的步数 |
| batch_size | 64 |  |
| gamma | 0.99 | 折扣因子 |
| total_timesteps | 1_000_000 | 约1-2小时训练（RTX 3060）|

**也可以试试 SAC**：通常在连续控制任务上表现更好，但训练更慢。

## 六、使用方式

### 训练

```bash
cd <项目路径>/robot/software/genbot_rl
uv run python scripts/train.py
```

### 查看训练曲线

```bash
uv run python scripts/train.py --eval
```
或者用 TensorBoard：
```bash
tensorboard --logdir models/tensorboard/
```

### 测试已训练的策略

```bash
uv run python scripts/test.py --model models/nav_policy.zip --episodes 10
```

### 可视化

```bash
uv run python scripts/test.py --model models/nav_policy.zip --render
```

## 七、预期效果

经过 1M 步训练（约1-2小时）：
- 机器人能从随机起点导航到随机目标点
- 能避开墙壁和障碍物
- 成功率 > 80%
- 能适应不同起始位置和目标位置

## 八、后续优化方向

| 方向 | 说明 |
|------|------|
| 更复杂的障碍物布局 | 随机生成墙壁/迷宫 |
| 领域随机化 | 摩擦系数、质量、地面颜色等 |
| 迁移到 Gazebo | 把 SB3 策略部署到 Gazebo 中验证 |
| 迁移到实物 | ros2_control + SB3 策略推理 |
| 视觉导航 | 增加相机输入，用 CNN 策略 |

---

*文档版本: 2026-05-24*
