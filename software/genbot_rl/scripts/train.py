"""
GenBot MuJoCo RL 训练脚本

用法:
    uv run python scripts/train.py              # 训练
    uv run python scripts/train.py --eval       # 训练完后评估
    uv run python scripts/train.py --load models/nav_policy.zip  # 继续训练
"""

import os
import sys
import argparse
import numpy as np
from stable_baselines3 import PPO, SAC
from stable_baselines3.common.callbacks import (
    CheckpointCallback,
    EvalCallback,
    StopTrainingOnRewardThreshold,
)
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from envs.genbot_env import GenBotNavEnv


def make_env(render=False):
    """创建环境的工厂函数"""
    render_mode = "human" if render else None
    return GenBotNavEnv(render_mode=render_mode)


def train(args):
    """训练导航策略"""
    print("=" * 50)
    print("GenBot MuJoCo RL 导航训练")
    print("=" * 50)

    # 创建训练环境
    env = DummyVecEnv([lambda: Monitor(GenBotNavEnv())])

    # 创建评估环境
    eval_env = DummyVecEnv([lambda: Monitor(GenBotNavEnv())])

    # 保存路径
    save_dir = args.save_dir
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(os.path.join(save_dir, "tensorboard"), exist_ok=True)

    # 回调: 定期保存
    checkpoint_callback = CheckpointCallback(
        save_freq=50000,
        save_path=save_dir,
        name_prefix="genbot_nav",
    )

    # 回调: 评估
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=save_dir,
        log_path=save_dir,
        eval_freq=20000,
        deterministic=True,
        render=False,
        n_eval_episodes=10,
    )

    # 选择算法
    if args.algo == "ppo":
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=args.lr,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            policy_kwargs=dict(
                net_arch=dict(pi=[256, 256], vf=[256, 256]),
            ),
            verbose=1,
            tensorboard_log=os.path.join(save_dir, "tensorboard"),
            seed=args.seed,
        )
    elif args.algo == "sac":
        model = SAC(
            "MlpPolicy",
            env,
            learning_rate=args.lr,
            buffer_size=200000,
            batch_size=256,
            tau=0.005,
            gamma=0.99,
            policy_kwargs=dict(
                net_arch=dict(pi=[256, 256], qf=[256, 256]),
            ),
            verbose=1,
            tensorboard_log=os.path.join(save_dir, "tensorboard"),
            seed=args.seed,
        )
    else:
        raise ValueError(f"Unknown algorithm: {args.algo}")

    # 加载已有模型（继续训练）
    if args.load:
        print(f"加载已有模型: {args.load}")
        if args.algo == "ppo":
            model = PPO.load(args.load, env=env)
        else:
            model = SAC.load(args.load, env=env)

    print(f"\n算法: {args.algo.upper()}")
    print(f"总步数: {args.timesteps}")
    print(f"学习率: {args.lr}")
    print(f"保存路径: {save_dir}")
    print(f"TensorBoard: {os.path.join(save_dir, 'tensorboard')}")
    print()

    # 开始训练
    model.learn(
        total_timesteps=args.timesteps,
        callback=[checkpoint_callback, eval_callback],
        progress_bar=True,
    )

    # 保存最终模型
    final_path = os.path.join(save_dir, "nav_policy_final.zip")
    model.save(final_path)
    print(f"\n✅ 训练完成! 模型已保存: {final_path}")

    # 评估
    if args.eval:
        evaluate(model, args)


def evaluate(model_or_path, args=None):
    """评估策略"""
    if isinstance(model_or_path, str):
        env = DummyVecEnv([lambda: Monitor(GenBotNavEnv())])
        model = PPO.load(model_or_path, env=env)
    else:
        model = model_or_path
        env = model.env

    num_episodes = 10
    successes = 0
    total_rewards = []
    total_steps = []

    print(f"\n{'='*50}")
    print(f"评估策略 ({num_episodes} episodes)")
    print(f"{'='*50}")

    for ep in range(num_episodes):
        obs = env.reset()
        done = False
        ep_reward = 0
        ep_steps = 0

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            ep_reward += reward[0]
            ep_steps += 1

        total_rewards.append(ep_reward)
        total_steps.append(ep_steps)

        # 判断是否成功（到达目标）
        # 环境在到达目标时返回 reward >= 100
        success = ep_reward >= 80
        if success:
            successes += 1

        print(f"  Episode {ep+1}: reward={ep_reward:.1f}, steps={ep_steps}, {'✅' if success else '❌'}")

    success_rate = successes / num_episodes * 100
    avg_reward = np.mean(total_rewards)
    avg_steps = np.mean(total_steps)

    print(f"\n{'='*50}")
    print(f"评估结果:")
    print(f"  成功率: {success_rate:.0f}%")
    print(f"  平均奖励: {avg_reward:.1f}")
    print(f"  平均步数: {avg_steps:.0f}")
    print(f"{'='*50}")

    return success_rate


def test(args):
    """可视化测试"""
    from envs.genbot_env import GenBotNavEnv

    env = GenBotNavEnv(render_mode="human")
    model = PPO.load(args.load)

    num_episodes = args.episodes

    for ep in range(num_episodes):
        obs, _ = env.reset()
        done = False
        ep_reward = 0
        ep_steps = 0

        print(f"\nEpisode {ep+1} — 按 Ctrl+C 跳过")

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _ = env.step(action)
            ep_reward += reward
            ep_steps += 1
            done = terminated or truncated

        print(f"  Done! reward={ep_reward:.1f}, steps={ep_steps}")

    env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GenBot MuJoCo RL 训练")
    parser.add_argument("--algo", type=str, default="ppo", choices=["ppo", "sac"],
                        help="算法: PPO 或 SAC")
    parser.add_argument("--timesteps", type=int, default=1_000_000,
                        help="训练总步数")
    parser.add_argument("--lr", type=float, default=3e-4,
                        help="学习率")
    parser.add_argument("--save-dir", type=str, default="models",
                        help="模型保存目录")
    parser.add_argument("--load", type=str, default=None,
                        help="加载已有模型路径（继续训练）")
    parser.add_argument("--eval", action="store_true",
                        help="训练完后评估")
    parser.add_argument("--seed", type=int, default=42,
                        help="随机种子")

    # 测试模式
    parser.add_argument("--test", action="store_true",
                        help="测试模式（可视化）")
    parser.add_argument("--episodes", type=int, default=5,
                        help="测试轮数")

    args = parser.parse_args()

    if args.test:
        # 仅测试
        if not args.load:
            args.load = "models/nav_policy_final.zip"
        test(args)
    else:
        # 训练
        train(args)
