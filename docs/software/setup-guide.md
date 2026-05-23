# 环境搭建指南

> 适用：Ubuntu 22.04 + ROS2 Humble + Gazebo Harmonic（gz-sim 8）

---

## 一、环境要求

| 项目 | 要求 | 已验证 |
|------|------|--------|
| 操作系统 | Ubuntu 22.04 LTS (Jammy) | ✅ |
| ROS2 | Humble Hawksbill (LTS 2022-2027) | ✅ |
| Gazebo | Harmonic (gz-sim 8) | ✅（预装） |
| Python | 3.10+ | ✅ |
| GPU（可选） | NVIDIA + 驱动（用于Gazebo渲染和AI推理） | 待修复 |

---

## 二、ROS2 Humble 安装确认

```bash
source /opt/ros/humble/setup.bash
ros2 pkg list | head -5
```

如果已装，跳过。否则按 [ROS2 Humble 官方文档](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html) 安装。

---

## 三、安装所需 ROS2 包

### 3.1 安装命令

```bash
sudo apt install -y \
  ros-humble-ros-gzharmonic-sim \
  ros-humble-ros-gzharmonic-bridge \
  ros-humble-xacro \
  ros-humble-joint-state-publisher-gui \
  ros-humble-rviz2 \
  ros-humble-nav2-bringup \
  ros-humble-slam-toolbox \
  ros-humble-robot-localization \
  ros-humble-teleop-twist-keyboard
```

### 3.2 安装清单

| 包名 | 用途 | 状态 |
|------|------|------|
| `ros-humble-ros-gzharmonic-sim` | Gazebo Harmonic 仿真启动工具 | ✅ 已装 |
| `ros-humble-ros-gzharmonic-bridge` | ROS2 ↔ Gazebo 话题桥接 | ✅ 已装 |
| `ros-humble-xacro` | URDF 宏预处理工具 | ✅ 已装 |
| `ros-humble-joint-state-publisher-gui` | 关节状态发布器（调试用GUI） | ✅ 已装 |
| `ros-humble-rviz2` | 3D可视化工具 | ✅ 已装 |
| `ros-humble-nav2-bringup` | Nav2 导航栈启动包 | ✅ 已装 |
| `ros-humble-slam-toolbox` | SLAM建图工具 | ✅ 已装 |
| `ros-humble-robot-localization` | 里程计融合（EKF） | ✅ 已装 |
| `ros-humble-teleop-twist-keyboard` | 键盘遥控 | ✅ 已装 |

> **注意：** 系统预装的是 Gazebo Harmonic（gz-sim 8）而非 Gazebo Classic。
> 因此不使用 `ros-humble-gazebo-ros-pkgs`（它与 gz-harmonic 冲突）。
> 改用 `ros-gzharmonic-*` 桥接包。

### 3.3 验证安装

```bash
source /opt/ros/humble/setup.bash

# 检查各包是否可用
ros2 pkg list | grep -iE "gzharmonic|nav2_bringup|slam_toolbox|robot_localization|xacro"

# 检查 gz-sim
gz sim --help

# 验证 xacro 解析 URDF
colcon build --packages-select genbot_description
source install/setup.bash
ros2 run xacro xacro software/genbot_description/urdf/genbot.urdf.xacro | head -10
```

---

## 四、项目编译

### 4.1 首次编译

```bash
cd /media/zsq-508/data/project/robot
colcon build --packages-select genbot_description
source install/setup.bash
```

### 4.2 更新后重新编译

```bash
colcon build --packages-select genbot_description --cmake-clean-first
source install/setup.bash
```

---

## 五、运行验证

### 5.1 RViz 中查看模型

```bash
ros2 launch genbot_description display.launch.py
```

### 5.2 Gazebo 中启动

```bash
ros2 launch genbot_description gazebo.launch.py
```

### 5.3 键盘控制

```bash
# 另开终端
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### 5.4 建图与导航

（后续 Phase 2 补充 Nav2 启动方法）

---

## 六、已知问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `nvidia-smi` 报错驱动版本不匹配 | NVIDIA 驱动 DKMS 构建失败 | 需修复驱动后重启 |
| Gazebo Harmonic 渲染可能有性能问题 | 禁用 NVIDIA 驱动后使用 llvmpipe | 修复 NVIDIA 驱动即可 |

---

## 七、文件结构

```
robot/
├── software/genbot_description/     # URDF 模型包
│   ├── urdf/genbot.urdf.xacro       # 主模型文件
│   ├── urdf/genbot.gazebo.xacro     # Gazebo 插件配置
│   ├── launch/gazebo.launch.py      # Gazebo 启动
│   ├── launch/display.launch.py     # RViz 启动
│   ├── worlds/genbot.world          # 测试场景
│   └── rviz/genbot.rviz             # RViz 预设
├── firmware/                        # ESP32 固件（待开发）
├── software/                        # 上层软件（ROS2 / AI）
└── docs/                            # 文档
```

---

*文档版本: 2026-05-23*
