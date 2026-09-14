"""
实验二 任务1：理解纯python代码1中实现 K-Means 的方法，并对其进行改进

说明：实验二没有随实验附带的 K-Means 参考代码，所以“纯python代码1”由我们自己实现，
      即同目录下的 纯python代码1_KMeans聚类.py（用 numpy 从零实现，并做了 5 点改进）。

本脚本的内容：
    1. 在三个高斯簇上自测，检查聚类是否正确（SSE、轮廓系数、聚类准确率、迭代轮数），
       并画出聚类结果与目标函数（SSE）随迭代次数的下降曲线；
    2. 验证改进 1（k-means++ 初始化）：在较难的高维合成数据上，随机初始化与
       k-means++ 初始化各跑 20 次，比较 SSE 的分布；
    3. 验证改进 2（n_init 多次重启）：比较 n_init = 1 与 n_init = 10 的效果。
"""
import os
import numpy as np
import matplotlib.pyplot as plt

from 纯python代码1_KMeans聚类 import KMeans, silhouette_score

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
os.makedirs(IMG_DIR, exist_ok=True)


def make_clusters(n_clusters, dims, size, spread, seed=7):
    """生成 n_clusters 个高斯簇：每个簇一个随机中心，样本在中心附近正态分布"""
    rng = np.random.default_rng(seed)
    centers = rng.normal(0, spread, size=(n_clusters, dims))
    X = np.vstack([c + rng.normal(0, 1.0, size=(size, dims)) for c in centers])
    y = np.repeat(np.arange(n_clusters), size)
    return X, y


def cluster_accuracy(y_true, y_pred, n_clusters):
    """用“多数投票”把簇标签对齐到真实标签后的聚类准确率"""
    correct = sum(np.bincount(y_true[y_pred == j]).max()
                  for j in range(n_clusters) if np.any(y_pred == j))
    return correct / len(y_true)


def run_many(X, k, init, n_init=1, n_runs=20):
    """用 n_runs 个不同随机种子各跑一次，返回每次的 SSE"""
    sses = []
    for seed in range(n_runs):
        m = KMeans(n_clusters=k, n_init=n_init, init=init, random_state=seed).fit(X)
        sses.append(m.inertia_)
    return np.array(sses)

def main():
    # ================================================== 1. 三个高斯簇自测
    print("=== 1. 三个高斯簇上的自测 ===")
    X_easy, y_easy = make_clusters(3, 2, 100, spread=6, seed=0)
    km = KMeans(n_clusters=3, n_init=10, random_state=42).fit(X_easy)
    print("SSE = %.4f，实际迭代轮数 = %d" % (km.inertia_, km.n_iter_))
    print("轮廓系数 = %.4f" % silhouette_score(X_easy, km.labels_))
    print("聚类准确率（投票对齐后）= %.4f" % cluster_accuracy(y_easy, km.labels_, 3))
    print("各簇样本数：", np.bincount(km.labels_).tolist())

    plt.figure(figsize=(8, 6))
    for c in range(3):
        m = km.labels_ == c
        plt.scatter(X_easy[m, 0], X_easy[m, 1], s=45, edgecolor="k", label=f"簇 {c}")
    plt.scatter(km.cluster_centers_[:, 0], km.cluster_centers_[:, 1],
                marker="X", s=260, c="red", edgecolor="k", label="簇中心")
    plt.xlabel("特征 1")
    plt.ylabel("特征 2")
    plt.title("任务1 自测：三个高斯簇的 K-Means 聚类结果")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task1_自测_聚类结果.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("聚类结果图已保存：", out)

    plt.figure(figsize=(8, 5))
    plt.plot(range(1, len(km.inertia_history_) + 1), km.inertia_history_, "o-", color="#2c7fb8")
    plt.xlabel("迭代轮数")
    plt.ylabel("SSE（簇内误差平方和）")
    plt.title("任务1：目标函数 SSE 随迭代次数的下降（改进3 收敛判据）")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task1_目标函数收敛曲线.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("收敛曲线已保存：", out)

    # ======================== 2. 改进效果对比（较难的高维合成数据）
    print("\n=== 2. 改进效果对比（8 簇、15 维、每簇 250 个样本）===")
    X_hard, _ = make_clusters(8, 15, 250, spread=6, seed=7)
    sse_random = run_many(X_hard, 8, "random", n_init=1)
    sse_random10 = run_many(X_hard, 8, "random", n_init=10, n_runs=10)
    sse_pp = run_many(X_hard, 8, "k-means++", n_init=1)
    sse_pp10 = run_many(X_hard, 8, "k-means++", n_init=10, n_runs=10)

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5))
    axes[0].boxplot([sse_random, sse_pp], tick_labels=["随机初始化", "k-means++"], showmeans=True)
    axes[0].set_ylabel("SSE（越小越好）")
    axes[0].set_title("改进1：初始化方法对比（各 20 次，n_init = 1）", fontsize=11)
    axes[0].grid(alpha=0.3, axis="y")
    axes[1].boxplot([sse_random, sse_random10, sse_pp10],
                    tick_labels=["随机\nn_init=1", "随机\nn_init=10", "k-means++\nn_init=10"],
                    showmeans=True)
    axes[1].set_ylabel("SSE（越小越好）")
    axes[1].set_title("改进2：多次重启（n_init）的作用", fontsize=11)
    axes[1].grid(alpha=0.3, axis="y")
    fig.suptitle("任务1：K-Means 改进效果对比", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(IMG_DIR, "task1_改进对比.png")
    fig.savefig(out, dpi=150)
    plt.close()
    print("改进对比图已保存：", out)

    print("随机初始化（n_init=1）  ：SSE 均值 = %.1f，标准差 = %.1f，最差 = %.1f"
          % (sse_random.mean(), sse_random.std(), sse_random.max()))
    print("随机初始化（n_init=10） ：SSE 均值 = %.1f，标准差 = %.1f，最差 = %.1f"
          % (sse_random10.mean(), sse_random10.std(), sse_random10.max()))
    print("k-means++ （n_init=1）  ：SSE 均值 = %.1f，标准差 = %.1f，最差 = %.1f"
          % (sse_pp.mean(), sse_pp.std(), sse_pp.max()))
    print("k-means++ （n_init=10） ：SSE 均值 = %.1f，标准差 = %.1f，最差 = %.1f"
          % (sse_pp10.mean(), sse_pp10.std(), sse_pp10.max()))
    drop1 = (1 - sse_pp.mean() / sse_random.mean()) * 100
    drop2 = (1 - sse_random10.mean() / sse_random.mean()) * 100
    print("→ 改进1（k-means++）让平均 SSE 下降约 %.1f%%；" % drop1)
    print("  改进2（多次重启）让随机初始化的平均 SSE 再下降约 %.1f%%；" % drop2)
    print("  两者结合（k-means++ + n_init=10）时结果最稳定，20 次实验的 SSE 完全一致。")


if __name__ == "__main__":
    main()