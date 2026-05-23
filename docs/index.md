# GenBot — 从零制作具身机器人

> **GenBot** (Generation Robot) — 一个开源的通用机器人开发平台。
> 从底盘驱动到AI决策，全程开源分享。

---

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![ROS2](https://img.shields.io/badge/ROS2-Humble-22314E?logo=ros)](https://docs.ros.org/en/humble/)
[![Platform](https://img.shields.io/badge/Platform-ESP32+Jetson-green)](docs/electrical/tech-report.md)
[![Status](https://img.shields.io/badge/Status-Planning-blue)](docs/PLAN.md)

---

## 项目愿景

**三步走路线：**

```
轮式/履带原型  ──→  人形机器人  ──→  多模态智能体
     ↓                  ↓                ↓
  运动控制基础       关节控制         多感官融合
  SLAM/导航         双足平衡         统一认知架构
  感知+AI基础       上层AI迁移       多形态协作
```

## 当前进度：Phase 0 — 仿真与固件学习

[![Phase 0](https://img.shields.io/badge/Phase-0-blueviolet)](docs/PLAN.md)
![Simulation](https://img.shields.io/badge/Sim-Ubuntu+ROS2+Gazebo-orange)
![Firmware](https://img.shields.io/badge/FW-ESP32+Arduino-critical)

- ✅ 项目规划完成
- ✅ 硬件选型确定（4轮差速/SP32/TB6612）
- ✅ 底层技术报告发布
- ⬜ 仿真环境搭建
- ⬜ ESP32固件入门
- ⬜ 硬件采购

## 技术架构

```ascii
┌───────────────────────────────────────┐
│           AI / 云端推理层              │
│   LLM Agent · 视觉检测 · 任务规划      │
└──────────────┬────────────────────────┘
               │  WiFi / 4G
┌──────────────┴────────────────────────┐
│       核心计算 (Jetson Orin)           │
│  ROS2 · SLAM · Nav2 · 多模态感知       │
└──────────────┬────────────────────────┘
               │  UART / USB
┌──────────────┴────────────────────────┐
│       实时控制 (ESP32)                 │
│  电机PID · 编码器 · IMU · 安全保护     │
└──────────────┬────────────────────────┘
               │  PWM / 编码器
┌──────────────┴────────────────────────┐
│      执行器与传感器                    │
│  直流有刷电机 · LiDAR · RGB-D相机      │
└───────────────────────────────────────┘
```

## 硬件选型 (v1.0)

| 组件 | 选型 | 备注 |
|------|------|------|
| 底盘 | 4轮差速两驱 | 成本低+里程计准 |
| 电机 | JGA25-371编码电机 | 有刷+AB相，零固件友好 |
| 驱动 | TB6612FNG | MOSFET高效驱动 |
| 底层控制 | ESP32-DevKitC V4 | Arduino框架入门 |
| 主控 | Jetson Orin Nano (8GB) | 视觉AI推理 |
| 建图 | RPLIDAR A1 + Realsense D435 | 2D SLAM + 深度感知 |
| IMU | MPU6050 | 6轴姿态估计 |

## 项目结构

```
robot/
├── docs/           # 所有文档（也是GitHub Pages源）
│   ├── PLAN.md              # 总体规划
│   ├── design-notes.md      # 设计讨论记录
│   ├── electrical/          # 电路技术文档
│   ├── mechanical/          # 机械设计文档
│   └── software/            # 软件设计文档
├── cad/            # CAD模型
├── pcb/            # PCB设计
├── firmware/       # ESP32固件
├── software/       # 上层软件+AI
└── materials/      # 物料清单
```

## 快速链接

| 目的 | 链接 |
|------|------|
| 了解全局规划 | [总体规划](docs/PLAN.md) |
| 底层技术选型 | [技术报告](docs/electrical/tech-report.md) |
| 为何选4轮差速 | [底盘决策](docs/mechanical/chassis-decision.md) |
| 设计讨论记录 | [设计笔记](docs/design-notes.md) |

## 参与贡献

本项目完全开源，欢迎：
- ⭐ Star 关注项目进展
- 🐛 提交 Issue 报告问题或建议
- 🔧 提交 PR 贡献代码

---

*Built with ❤️ by [Shuaiqing Zhang](https://github.com/zhangshuaiqing)*
