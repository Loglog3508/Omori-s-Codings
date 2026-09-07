"""
实验一 任务1：使用 Python 实现阶跃函数和 Sigmoid 函数，并将其可视化
"""
import numpy as np
import matplotlib.pyplot as plt

# 设置中文字体，避免绘图时中文乱码
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

import os
os.makedirs(os.path.join(os.path.dirname(__file__), "结果图"), exist_ok=True)


def step_function(x):
    """阶跃函数：x > 0 时输出 1，否则输出 0"""
    return np.where(x > 0, 1.0, 0.0)


def sigmoid(x):
    """Sigmoid 函数：f(x) = 1 / (1 + e^(-x))"""
    # 数值稳定写法：对较大的负数使用 exp(x) / (1 + exp(x))
    return np.where(
        x >= 0,
        1.0 / (1.0 + np.exp(-x)),
        np.exp(x) / (1.0 + np.exp(x)),
    )


def main():
    x = np.linspace(-10, 10, 400)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

    # 左图：阶跃函数
    axes[0].plot(x, step_function(x), linewidth=2, color="#2c7fb8")
    axes[0].axhline(0, color="gray", lw=0.8, ls="--")
    axes[0].axhline(1, color="gray", lw=0.8, ls="--")
    axes[0].axvline(0, color="gray", lw=0.8, ls="--")
    axes[0].set_title("阶跃函数 (Step Function)")
    axes[0].set_xlabel("x")
    axes[0].set_ylabel("f(x)")
    axes[0].set_ylim(-0.15, 1.15)
    axes[0].grid(alpha=0.3)

    # 右图：Sigmoid 函数
    y_sig = sigmoid(x)
    axes[1].plot(x, y_sig, linewidth=2, color="#e6550d")
    axes[1].axhline(0.5, color="gray", lw=0.8, ls="--")
    axes[1].axhline(1, color="gray", lw=0.8, ls="--")
    axes[1].axvline(0, color="gray", lw=0.8, ls="--")
    axes[1].set_title("Sigmoid 函数 (Sigmoid Function)")
    axes[1].set_xlabel("x")
    axes[1].set_ylabel("f(x)")
    axes[1].set_ylim(-0.05, 1.05)
    axes[1].grid(alpha=0.3)

    # 标注关键点
    axes[1].annotate("σ(0) = 0.5", xy=(0, 0.5), xytext=(-6.5, 0.7),
                     arrowprops=dict(arrowstyle="->"), fontsize=10)

    fig.suptitle("阶跃函数与 Sigmoid 函数", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    out_path = os.path.join(os.path.dirname(__file__), "结果图", "task1_阶跃函数与sigmoid.png")
    fig.savefig(out_path, dpi=150)
    print("图像已保存：", out_path)

    # 打印几个关键取值，方便报告引用
    print("sigmoid(-10) =", round(float(sigmoid(-10)), 6))
    print("sigmoid(0)   =", round(float(sigmoid(0)), 6))
    print("sigmoid(10)  =", round(float(sigmoid(10)), 6))


if __name__ == "__main__":
    main()
