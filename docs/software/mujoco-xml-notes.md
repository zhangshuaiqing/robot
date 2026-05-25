# MuJoCo 四轮阿克曼底盘 XML 建模笔记

## 关键知识点

### 1. MuJoCo 中 cylinder 几何体的默认朝向

`<geom type="cylinder" size="r h"/>` 中，圆柱的**对称轴始终是 Z 轴**（在 body 的局部坐标系中）。`size` 的两个参数分别是：
- `r`：底面半径
- `h`：沿 Z 轴方向的半高（即总高度 = 2h）

要让 cylinder 作为车轮水平放置（像真实车轮一样），需要：
- 方案A：用 `body` 的 `quat` 或 `euler` 属性旋转整个 body，使圆柱轴指向 Y 或 X 方向
- 方案B：因为 MuJoCo 的 `cylinder` 接触计算只对侧面有效，顶面和底面不会产生正确的滚动摩擦，所以**很多开源四轮车模型直接用 `sphere` 做轮子**

### 2. 为什么 sphere 比 cylinder 更适合做轮子

MuJoCo 中 sphere 的接触计算是最简单最稳定的：
- 球体在任何方向上的摩擦力对称，不需要考虑旋转轴对齐问题
- 球体与平面的接触是一个点，无论球体怎么转，接触计算都一样
- cylinder 的接触是线接触，如果轴不对齐或者车身倾斜，容易出现接触抖动
- Google DeepMind 官方示例、gymnasium 中的车辆类环境大多使用 sphere 做轮子

### 3. 阿克曼转向在 MuJoCo 中的实现

阿克曼转向的核心：
- **前轮**：通过 `hinge` 关节（axis=0 0 1）实现绕Z轴转向，用 `position` actuator 控制转向角
- **后轮**：用 `motor` actuator 驱动（对于 sphere 无方向问题，直接加力矩即可）
- **左右转角不同**：在环境代码（Python）中按阿克曼几何公式计算左右轮各自的转向角，分别控制两个 steering joint

参考：F1TENTH 的 MuJoCo 版本、Google 的 `mujoco_menagerie` 中的车辆模型、各种 gymnasium MuJoCo 环境。
