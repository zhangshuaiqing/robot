#!/usr/bin/env python3
"""在 MuJoCo viewer 中查看 GenBot 阿克曼底盘（10秒）"""

import mujoco
import mujoco.viewer
import time
import math
import sys

model = mujoco.MjModel.from_xml_path(
    "/media/zsq-508/data/project/robot/software/genbot_rl/xml/genbot_ackermann.xml"
)
data = mujoco.MjData(model)

print(f"模型: {model.nu} actuators, {model.nbody} bodies")
for i in range(model.nu):
    print(f"  actuator[{i}]: {model.actuator(i).name}")
sys.stdout.flush()

print("🔄 窗口打开10秒，观察前进+转向")
sys.stdout.flush()

with mujoco.viewer.launch_passive(model, data) as viewer:
    viewer.cam.distance = 2.0
    viewer.cam.azimuth = 60
    viewer.cam.elevation = -30

    start = time.time()
    while viewer.is_running() and time.time() - start < 10:
        t = time.time() - start

        # 后轮驱动（前进）
        data.ctrl[0] = 3.0   # left_motor
        data.ctrl[1] = 3.0   # right_motor

        # 前轮阿克曼转向（左右摆动）
        steer = 0.3 * math.sin(t * 1.5)
        data.ctrl[2] = steer * 1.2   # fl_steer_act（内轮，转角大）
        data.ctrl[3] = steer * 0.8   # fr_steer_act（外轮，转角小）

        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(0.01)

print("✅ 结束")
