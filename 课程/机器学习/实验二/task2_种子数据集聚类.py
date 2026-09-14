"""
实验二 任务2：用纯python代码对种子数据集进行聚类

数据集（老师提供）：KMeans/纯python代码1/seeds_dataset.txt —— UCI 小麦种子数据集（Seeds）
    - 样本数：210
    - 特征数：7（面积、周长、紧密度、籽粒长度、籽粒宽度、不对称系数、腹沟长度）
    - 类别数：3（Kama / Rosa / Canadian 三个小麦品种，每类 70 个样本）
    - 文件格式：制表符分隔，前 7 列是特征，最后一列是品种编号 1/2/3

用到的两份老师提供的纯python代码：
    代码1：KMeans/纯python代码1/kmeans.py（面向对象写法 KMeans + k-means++ + 多次重启）
    代码2：KMeans/纯python代码2/kmeans_utils.py（函数式写法 init_centroids / e_step / m_step）

流程：
    1. 读取 seeds_dataset.txt；
    2. 特征标准化（z-score）——K-Means 基于欧氏距离，对特征量纲敏感；
    3. 分别用代码1、代码2 聚类，并对比两者的结果；
    4. 评估：SSE、轮廓系数、与真实品种对比（混淆矩阵、聚类准确率、ARI、NMI）；
    5. 可视化：肘部曲线与轮廓系数、PCA 二维聚类结果、混淆矩阵、代码1/代码2 对比。
"""
import os
import sys
import warnings
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import PCA
from sklearn.metrics import (adjusted_rand_score, normalized_mutual_info_score,
                             confusion_matrix, ConfusionMatrixDisplay)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
os.makedirs(IMG_DIR, exist_ok=True)

# 把老师提供的两份纯python代码加入搜索路径，直接复用其中的函数
sys.path.insert(0, os.path.join(BASE, "KMeans", "纯python代码1"))
sys.path.insert(0, os.path.join(BASE, "KMeans", "纯python代码2"))
# 兼容补丁：老师代码用了 np.int 与 np.object，这两个别名在 NumPy 2.x 中已被移除
np.int, np.object = int, object
from kmeans import KMeans as TeacherKMeans            # noqa: E402  老师提供的代码1
import kmeans_utils                                    # noqa: E402  老师提供的代码2

sys.path.insert(0, BASE)
from 纯python代码1_KMeans改进版 import ImprovedKMeans, silhouette_score  # noqa: E402

CLASS_NAMES = ["Kama", "Rosa", "Canadian"]


def load_seeds(path):
    """读取老师提供的 seeds_dataset.txt：前 7 列是特征，最后一列是类别（1/2/3）"""
    data = np.loadtxt(path)
    X = data[:, :7]
    y = data[:, 7].astype(int) - 1            # 类别 1/2/3 → 0/1/2
    return X, y


def standardize(X):
    """z-score 标准化"""
    mean, std = X.mean(axis=0), X.std(axis=0)
    std[std == 0] = 1.0
    return (X - mean) / std


def align_labels(y_true, y_pred, n_clusters):
    """用匈牙利算法把簇编号对齐到真实类别（最大化一致样本数），用于计算聚类准确率"""
    cm = confusion_matrix(y_true, y_pred, labels=list(range(n_clusters)))
    row, col = linear_sum_assignment(-cm)      # 求最大权匹配（取负号变成最小化）
    mapping = {c: r for r, c in zip(row, col)}
    return np.array([mapping[c] for c in y_pred]), mapping


def evaluate(y, labels, X, k, name):
    """统一计算一组聚类评估指标"""
    y_aligned, mapping = align_labels(y, labels, k)
    res = {
        "name": name,
        "轮廓系数": silhouette_score(X, labels),
        "聚类准确率": float(np.mean(y_aligned == y)),
        "ARI": float(adjusted_rand_score(y, labels)),
        "NMI": float(normalized_mutual_info_score(y, labels)),
    }
    print("  [%s] 轮廓系数=%.4f  聚类准确率=%.4f  ARI=%.4f  NMI=%.4f"
          % (name, res["轮廓系数"], res["聚类准确率"], res["ARI"], res["NMI"]))
    return res, y_aligned, mapping


def run_utils_kmeans(X, k, max_iters=100, seed=42):
    """复用老师“纯python代码2”的 init_centroids / e_step / m_step 跑一遍 K-Means

    老师的 m_step 对空簇会算出 nan（0 除以 0），这里遇到空簇就沿用旧中心，
    保证循环能正常收敛；这与代码1 里“空簇则返回 None”的处理有所不同。
    """
    np.random.seed(seed)
    centroids = kmeans_utils.init_centroids(X, k)
    j_history = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for _ in range(max_iters):
            r, j_value = kmeans_utils.e_step(X, centroids)
            j_history.append(float(j_value))
            new_centroids = kmeans_utils.m_step(X, r, k)
            bad = ~np.isfinite(new_centroids).all(axis=1)
            new_centroids[bad] = centroids[bad]
            converged = np.allclose(new_centroids, centroids)
            centroids = new_centroids
            if converged:
                break
        r, j_value = kmeans_utils.e_step(X, centroids)
        j_history.append(float(j_value))
    return r, centroids, float(j_value), j_history


def main():
    # ---------------------------------------------------------- 1. 读取数据
    X_raw, y = load_seeds(os.path.join(BASE, "KMeans", "纯python代码1", "seeds_dataset.txt"))
    print("种子数据集（老师提供）：", X_raw.shape, "，类别：", CLASS_NAMES)
    print("每类样本数：", np.bincount(y).tolist())

    X = standardize(X_raw)                     # 标准化后再聚类
    k = 3

    # ------------------------------------ 2. 用老师代码1（面向对象写法）聚类
    print("\n【代码1】KMeans/纯python代码1/kmeans.py —— KMeans 类（k-means++ + n_init 次重启）")
    np.random.seed(42)                         # 老师代码用 np.random，固定种子以便复现
    km1 = TeacherKMeans(k_clusters=k, n_init=10)
    labels1 = km1.predict(X)
    print("  SSE = %.4f，各簇样本数 = %s" % (km1.sse_, np.bincount(labels1).tolist()))
    res1, y_aligned1, mapping1 = evaluate(y, labels1, X, k, "代码1")
    print("  簇编号 → 真实品种：",
          {f"簇{c}": CLASS_NAMES[v] for c, v in sorted(mapping1.items())})

    # ------------------------------------ 3. 用老师代码2（函数式写法）聚类
    print("\n【代码2】KMeans/纯python代码2/kmeans_utils.py —— init_centroids / e_step / m_step")
    labels2, centers2, sse2, j_hist2 = run_utils_kmeans(X, k, seed=42)
    print("  SSE = %.4f，各簇样本数 = %s，迭代轮数 = %d"
          % (sse2, np.bincount(labels2, minlength=k).tolist(), len(j_hist2) - 1))
    res2, y_aligned2, mapping2 = evaluate(y, labels2, X, k, "代码2")
    print("  每轮目标函数 J：", [round(v, 2) for v in j_hist2])

    # ---------------------------- 4. 肘部法 + 轮廓系数选择 K（用改进版，可复现）
    print("\n不同 K 的聚类效果（用改进版跑，结果可复现）：")
    ks = list(range(2, 9))
    sse_list, sil_list = [], []
    for kk in ks:
        m = ImprovedKMeans(k_clusters=kk, n_init=10, random_state=42).fit(X)
        sse_list.append(m.sse_)
        sil_list.append(silhouette_score(X, m.labels_))
        print("  K=%d: SSE=%8.2f  轮廓系数=%.4f" % (kk, sse_list[-1], sil_list[-1]))

    fig, ax1 = plt.subplots(figsize=(8.5, 5))
    ax1.plot(ks, sse_list, "o-", color="#2c7fb8", label="SSE（簇内误差平方和）")
    ax1.set_xlabel("簇数 K")
    ax1.set_ylabel("SSE", color="#2c7fb8")
    ax1.tick_params(axis="y", labelcolor="#2c7fb8")
    ax1.axvline(3, color="gray", ls="--", lw=1)
    ax2 = ax1.twinx()
    ax2.plot(ks, sil_list, "s--", color="#e6550d", label="轮廓系数")
    ax2.set_ylabel("轮廓系数", color="#e6550d")
    ax2.tick_params(axis="y", labelcolor="#e6550d")
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [l.get_label() for l in lines], loc="center right")
    plt.title("种子数据集：肘部法与轮廓系数选择 K")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task2_种子数据集_肘部与轮廓系数.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("肘部/轮廓系数图已保存：", out)

    # ------------------------------------------------ 5. 可视化：PCA 二维
    X_pca = PCA(n_components=2, random_state=42).fit_transform(X)
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    for ax, labels, title, is_true in [
        (axes[0], labels1, "代码1 的聚类结果（簇编号）", False),
        (axes[1], labels2, "代码2 的聚类结果（簇编号）", False),
        (axes[2], y, "真实小麦品种", True),
    ]:
        for c in range(k):
            m = labels == c
            name = CLASS_NAMES[c] if is_true else f"簇 {c}"
            ax.scatter(X_pca[m, 0], X_pca[m, 1], s=45, edgecolor="k", label=name)
        ax.set_xlabel("主成分 1")
        ax.set_ylabel("主成分 2")
        ax.set_title(title)
        ax.legend()
        ax.grid(alpha=0.3)
    fig.suptitle("种子数据集 K-Means 聚类结果（PCA 降至 2 维）", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(IMG_DIR, "task2_种子数据集_聚类结果PCA.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("\nPCA 聚类结果图已保存：", out)

    # ------------------------------------------------ 6. 混淆矩阵
    cm = confusion_matrix(y, y_aligned1)
    disp = ConfusionMatrixDisplay(cm, display_labels=CLASS_NAMES)
    disp.plot(cmap="Blues")
    plt.title("种子数据集：代码1 聚类结果 vs 真实品种 混淆矩阵")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task2_种子数据集_混淆矩阵.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("混淆矩阵图已保存：", out)
    print("混淆矩阵（行=真实品种，列=聚类结果）：\n", cm)

    # ---------------------------------- 7. 代码1 与 代码2 的对比
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5))
    axes[0].bar(["代码1", "代码2"], [km1.sse_, sse2], color=["#2c7fb8", "#e6550d"], width=0.5)
    for i, v in enumerate([km1.sse_, sse2]):
        axes[0].text(i, v + 5, "%.2f" % v, ha="center", fontsize=10)
    axes[0].set_ylabel("SSE（越小越好）")
    axes[0].set_title("两份代码的 SSE 对比", fontsize=11)
    axes[0].grid(alpha=0.3, axis="y")

    metrics = ["轮廓系数", "聚类准确率", "ARI", "NMI"]
    xpos = np.arange(len(metrics))
    axes[1].bar(xpos - 0.18, [res1[m] for m in metrics], width=0.36, label="代码1")
    axes[1].bar(xpos + 0.18, [res2[m] for m in metrics], width=0.36, label="代码2")
    for i, m in enumerate(metrics):
        axes[1].text(i - 0.18, res1[m] + 0.015, "%.3f" % res1[m], ha="center", fontsize=8)
        axes[1].text(i + 0.18, res2[m] + 0.015, "%.3f" % res2[m], ha="center", fontsize=8)
    axes[1].set_xticks(xpos)
    axes[1].set_xticklabels(metrics)
    axes[1].set_ylim(0, 1)
    axes[1].set_title("两份代码的聚类指标对比", fontsize=11)
    axes[1].legend()
    axes[1].grid(alpha=0.3, axis="y")
    fig.suptitle("种子数据集：老师提供的代码1 与 代码2 对比", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(IMG_DIR, "task2_种子数据集_代码1与代码2对比.png")
    fig.savefig(out, dpi=150)
    plt.close()
    print("代码1/代码2 对比图已保存：", out)


if __name__ == "__main__":
    main()