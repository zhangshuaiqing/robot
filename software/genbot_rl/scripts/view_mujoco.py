#!/usr/bin/env python3
"""MuJoCo 中检查轮子旋转方向"""

import mujoco
import mujoco.viewer
import math
import time
import sys

model = mujoco.MjModel.from_xml_path(
    "/media/zsq-508/data/project/robot/software/genbot_rl/xml/genbot_ackermann.xml"
)
data = mujoco.MjData(model)

print("joint 列表:")
for i in range(model.njnt):
    jnt = model.joint(i)
    print(f"  [{i}] {jnt.name}  axis=({jnt.axis[0]:.2f},{jnt.axis[1]:.2f},{jnt.axis[2]:.2f})")
sys.stdout.flush()

print("actuator 列表:")
for i in range(model.nu):
    print(f"  [{i}] {model.actuator(i).name}")
sys.stdout.flush()

print("\n🔄 窗口已打开，观察5秒...")
sys.stdout.flush()

with mujoco.viewer.launch_passive(model, data) as viewer:
    viewer.cam.distance = 2.0
    viewer.cam.azimuth = 60
    viewer.cam.elevation = -30

    start = time.time()
    step = 0
    while viewer.is_running() and time.time() - start < 5:
        # 后轮驱动
        data.ctrl[0] = 3.0
        data.ctrl[1] = 3.0
        data.ctrl[2] = 0.0
        data.ctrl[3] = 0.0

        if step % 50 == 0:
            pos = data.body("chassis").xpos
            fl = data.joint("front_left_wheel").qpos[0]
            rl = data.joint("rear_left_wheel").qpos[0]
            print(f"  pos=({pos[0]:.3f},{pos[1]:.3f})  fl_wheel={fl:.2f}  rl_wheel={rl:.2f}")
            sys.stdout.flush()

        mujoco.mj_step(model, data)
        viewer.sync()
        step += 1
        time.sleep(0.01)

print("✅ 结束")
sys.stdout.flush()
