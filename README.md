# GenBot — 从零制作具身机器人

> **GenBot** (Generation Robot) — 一个开源的通用机器人开发平台。
> 从底盘驱动到AI决策，全程开源分享。

[![MIT License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![ROS2 Humble](https://img.shields.io/badge/ROS2-Humble-22314E)](https://docs.ros.org/en/humble/)
[![Phase 0](https://img.shields.io/badge/Phase-Planning-blueviolet)](docs/PLAN.md)
[![GitHub Pages](https://img.shields.io/badge/Pages-https://zhangshuaiqing.github.io/robot/-blue)](https://zhangshuaiqing.github.io/robot/)

---

**路线：** 轮式/履带原型 → 人形机器人 → 多模态智能体

**当前阶段：** Phase 0 — 仿真环境搭建 + 固件入门

---

## 快速开始

```bash
git clone git@github.com:zhangshuaiqing/robot.git
cd robot
```

详细规划见 [docs/PLAN.md](docs/PLAN.md) | 项目主页 → [zhangshuaiqing.github.io/robot](https://zhangshuaiqing.github.io/robot/)

## 目录结构

```
robot/
├── docs/           # 文档 + GitHub Pages 源
│   ├── index.md               # 项目主页
│   ├── PLAN.md                # 总体规划
│   ├── electrical/            # 电路与嵌入式
│   └── mechanical/            # 机械结构
├── firmware/       # ESP32 固件代码
├── software/       # 上层软件与AI
├── cad/            # CAD模型
├── pcb/            # PCB设计
└── materials/      # 物料清单
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 上层计算 | NVIDIA Jetson Orin + ROS2 Humble |
| 底层控制 | ESP32 + Arduino框架 |
| 电机驱动 | JGA25-371编码电机 + TB6612FNG |
| 感知 | RPLIDAR + Realsense D435 + MPU6050 |
| 仿真 | Gazebo Classic + Nav2 |
| AI | YOLO + LLM Agent (LangChain) |

## 许可证

[MIT](LICENSE) © 2026 Shuaiqing Zhang

