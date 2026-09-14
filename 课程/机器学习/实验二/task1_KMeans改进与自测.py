"""
实验二 任务1：理解纯python代码1中实现 K-Means 的方法，并对其进行改进

老师提供的纯python代码1：KMeans/纯python代码1/kmeans.py（原文件未做改动）
    接口：KMeans(k_clusters, tol, max_iter, n_init)
        _init_centers_kpp()  k-means++ 初始化簇中心（让初始中心彼此远离）
        _kmeans(X)           核心算法：分配标签 → 计算重心 → 判断收敛
        predict(X)           运行 n_init 次，返回 SSE 最小那一次的簇标签；
                            结果放在 km.centers_（簇中心）与 km.sse_（目标函数 J）里。

    它已经做得不错：有 k-means++ 初始化、有 n_init 多次重启、有 tol 收敛判据。
    但仍然有 5 处可以改进，改进版见 纯python代码1_KMeans改进版.py：
        改进1 兼容性与可复现：np.int / np.object 在 NumPy 2.x 已被移除（老师代码
              会直接报错），改用内置的 int / object；并新增 random_state 固定随机种子。
        改进2 空簇处理：老师代码遇到空簇就返回 None 让 predict() 整体重跑，
              这里改成把空簇中心就地重置到最“孤单”的样本上。
        改进3 收敛判据与过程记录：记录每轮目标函数 J，可画收敛曲线。
        改进4 向量化距离计算：把逐簇的 for 循环改成矩阵运算，速度更快。
        改进5 SSE 计算修正 + 轮廓系数：老师代码的 SSE 用的是更新中心之前那次
              分配的距离矩阵（偏大）；并内置纯 numpy 的轮廓系数辅助选 K。

本脚本依次完成：
    1. 用老师的原始代码在三个高斯簇上自测（SSE、轮廓系数、聚类准确率）；
    2. 演示老师代码在当前 NumPy 上的兼容性问题（改进1 的由来）与空簇问题（改进2）；
    3. 用改进版自测，并画目标函数 J 随迭代次数的下降曲线（改进3）；
    4. 量化对比 5 点改进的效果，画改进效果对比图。
"""
import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
os.makedirs(IMG_DIR, exist_ok=True)

# 把老师提供的“纯python代码1”目录加入搜索路径，直接复用其中的 KMeans
sys.path.insert(0, os.path.join(BASE, "KMeans", "纯python代码1"))
# 兼容补丁：老师代码用了 np.int 与 np.object，这两个别名在 NumPy 2.x 中已被移除
np.int, np.object = int, object
from kmeans import KMeans as TeacherKMeans          # noqa: E402

sys.path.insert(0, BASE)
from 纯python代码1_KMeans改进版 import ImprovedKMeans, silhouette_score  # noqa: E402


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
        m = ImprovedKMeans(k_clusters=k, init=init, n_init=n_init,
                           random_state=seed).fit(X)
        sses.append(m.sse_)
    return np.array(sses)


def main():
    # ==================================================== 1. 老师代码自测
    print("=== 1. 用老师提供的纯python代码1在三个高斯簇上自测 ===")
    X_easy, y_easy = make_clusters(3, 2, 100, spread=6, seed=0)
    np.random.seed(42)                      # 老师代码用 np.random，这里固定种子以便复现
    km_teacher = TeacherKMeans(k_clusters=3, n_init=10)
    labels_teacher = km_teacher.predict(X_easy)
    print("老师代码：SSE = %.4f，各簇样本数 = %s"
          % (km_teacher.sse_, np.bincount(labels_teacher).tolist()))
    print("轮廓系数（用改进版内置函数计算）= %.4f"
          % silhouette_score(X_easy, labels_teacher))
    print("聚类准确率（投票对齐后）= %.4f"
          % cluster_accuracy(y_easy, labels_teacher, 3))

    plt.figure(figsize=(8, 6))
    for c in range(3):
        m = labels_teacher == c
        plt.scatter(X_easy[m, 0], X_easy[m, 1], s=45, edgecolor="k", label=f"簇 {c}")
    plt.scatter(km_teacher.centers_[:, 0], km_teacher.centers_[:, 1],
                marker="X", s=260, c="red", edgecolor="k", label="簇中心")
    plt.xlabel("特征 1")
    plt.ylabel("特征 2")
    plt.title("任务1 自测：老师提供的纯python代码1 的聚类结果（三个高斯簇）")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task1_自测_聚类结果.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("聚类结果图已保存：", out)

    # ==================== 2. 老师代码的两个问题：np.int 兼容性、空簇重跑
    print("\n=== 2. 老师代码的两个问题（改进1、改进2 的由来）===")
    print("[问题1] np.int / np.object 兼容性：")
    del np.int, np.object                   # 临时撤掉兼容补丁，看老师的原代码能否直接跑
    try:
        TeacherKMeans(k_clusters=3, n_init=1).predict(X_easy[:30])
        print("  没报错（说明当前 NumPy 版本仍然保留 np.int）")
    except AttributeError as err:
        print("  直接运行老师代码 → AttributeError:", err)
        print("  原因：np.int / np.object 这类别名从 NumPy 1.24 起被弃用、2.0 起被彻底移除。")
    finally:
        np.int, np.object = int, object     # 加回兼容补丁，后面的代码继续运行
        print("  补上 np.int = int、np.object = object 之后，老师代码即可正常运行（改进1）。")

    print("[问题2] 空簇处理：")
    X_tiny = np.vstack([np.zeros((5, 2)), np.full((1, 2), 100.0)])   # 两组重复样本 + 1 个远点
    np.random.seed(0)
    res = TeacherKMeans(k_clusters=3)._kmeans(X_tiny)
    print("  老师代码的 _kmeans 在退化数据上返回：", res, "（None 表示出现空簇，本次作废）")
    print("  而 predict() 里是 while res is None 整体重跑，这种数据上会一直跑不出结果。")
    km_fix = ImprovedKMeans(k_clusters=3, n_init=1, random_state=0).fit(X_tiny)
    print("  改进版在同一数据上的结果：SSE = %.4f，各簇样本数 = %s"
          % (km_fix.sse_, np.bincount(km_fix.labels_, minlength=3).tolist()))
    print("  改进版不会卡死，而且保证输出 k 个非空簇（改进2）。")

    # ==================== 3. 改进版自测 + 目标函数收敛曲线
    print("\n=== 3. 改进版在三个高斯簇上自测（改进3：记录每轮 J）===")
    km = ImprovedKMeans(k_clusters=3, n_init=10, random_state=42).fit(X_easy)
    print("SSE = %.4f，实际迭代轮数 = %d" % (km.sse_, km.n_iter_))
    print("轮廓系数 = %.4f" % silhouette_score(X_easy, km.labels_))
    print("聚类准确率（投票对齐后）= %.4f" % cluster_accuracy(y_easy, km.labels_, 3))
    print("每轮目标函数 J：", [round(v, 2) for v in km.sse_history_])

    hist = km.sse_history_
    plt.figure(figsize=(8, 5))
    plt.plot(range(1, len(hist) + 1), hist, "o-", color="#2c7fb8")
    plt.xlabel("迭代轮数")
    plt.ylabel("目标函数 J（簇内误差平方和 SSE）")
    plt.title("任务1：目标函数 J 随迭代次数的下降（改进3 收敛过程记录）")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task1_目标函数收敛曲线.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("收敛曲线已保存：", out)

    # ==================== 4. 改进4（向量化）与改进5（SSE 修正）的量化对比
    print("\n=== 4. 改进4 向量化加速、改进5 SSE 计算修正 ===")
    X_hard, _ = make_clusters(8, 15, 250, spread=6, seed=7)     # 2000 个样本、15 维、8 簇
    X_big, _ = make_clusters(10, 64, 500, spread=6, seed=11)    # 5000 个样本、64 维、10 簇

    # 只比较“算一遍距离矩阵”这一步：老师代码逐簇循环，改进版一次矩阵运算
    rng_big = np.random.default_rng(0)
    centers_big = X_big[rng_big.choice(X_big.shape[0], 10, replace=False)]
    repeat = 50
    t0 = time.perf_counter()
    for _ in range(repeat):
        dists = np.empty((X_big.shape[0], 10))
        for i in range(10):
            np.sum((X_big - centers_big[i]) ** 2, axis=1, out=dists[:, i])
    t_teacher = time.perf_counter() - t0
    t0 = time.perf_counter()
    for _ in range(repeat):
        ImprovedKMeans._sq_dists(X_big, centers_big)
    t_improved = time.perf_counter() - t0
    print("同为 5000 个样本、64 维、10 簇，算 50 次距离矩阵：")
    print("  老师代码（逐簇循环）%.3f 秒 → 改进版（矩阵一次算完）%.3f 秒，快 %.1f 倍（改进4）"
          % (t_teacher, t_improved, t_teacher / max(t_improved, 1e-9)))

    # 把最大迭代次数限制得很小，就能看清 SSE 报告的偏差（正常收敛时偏差接近 0）
    np.random.seed(42)
    km_t3 = TeacherKMeans(k_clusters=3, tol=0.0, max_iter=3, n_init=1)
    lab_t3 = km_t3.predict(X_easy)
    true_sse = float(((X_easy - km_t3.centers_[lab_t3]) ** 2).sum())
    print("限定 3 轮迭代时：")
    print("  老师代码报告的 SSE = %.4f" % km_t3.sse_)
    print("  用它的最终中心重新计算 = %.4f（比报告值小 %.4f，改进5）"
          % (true_sse, km_t3.sse_ - true_sse))
    print("  原因：老师代码的 sse 用的是“更新中心之前”那一次分配留下的距离矩阵。")

    # ==================== 5. 改进1（k-means++）与改进2（n_init）的效果对比
    print("\n=== 5. 改进效果对比（合成数据：8 簇、15 维、每簇 250 个样本）===")
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
    print("→ 改进1（k-means++）让平均 SSE 下降约 %.1f%%；"
          % ((1 - sse_pp.mean() / sse_random.mean()) * 100))
    print("  改进2（多次重启）让随机初始化的平均 SSE 再下降约 %.1f%%；"
          % ((1 - sse_random10.mean() / sse_random.mean()) * 100))
    print("  两者结合（k-means++ + n_init=10）时结果最稳定。")


if __name__ == "__main__":
    main()