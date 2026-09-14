"""
实验二 任务2：用纯python代码对种子数据集进行聚类

数据集：UCI 小麦种子数据集（Seeds）
    - 样本数：210
    - 特征数：7（面积、周长、紧密度、籽粒长度、籽粒宽度、不对称系数、腹沟长度）
    - 类别数：3（Kama / Rosa / Canadian 三个小麦品种，每类 70 个样本）

流程：
    1. 读取 data/seeds.csv；
    2. 特征标准化（z-score）——K-Means 基于欧氏距离，对特征量纲敏感；
    3. 用纯python代码1中的 KMeans（k-means++ 初始化 + 多次重启）聚类；
    4. 评估：SSE、轮廓系数、与真实品种对比（混淆矩阵、聚类准确率、ARI、NMI）；
    5. 可视化：肘部曲线与轮廓系数、PCA 二维聚类结果、混淆矩阵。
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import PCA
from sklearn.metrics import (adjusted_rand_score, normalized_mutual_info_score,
                             confusion_matrix, ConfusionMatrixDisplay)

from 纯python代码1_KMeans聚类 import KMeans, silhouette_score

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
os.makedirs(IMG_DIR, exist_ok=True)


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


def choose_k(X, k_range=range(2, 9)):
    """肘部法 + 轮廓系数：遍历不同 K，返回 SSE 与轮廓系数"""
    sse, sil = [], []
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        sse.append(km.inertia_)
        sil.append(silhouette_score(X, km.labels_))
        print(f"  K={k}: SSE={km.inertia_:8.2f}  轮廓系数={sil[-1]:.4f}")
    return list(k_range), sse, sil

def main():
    # ---------------------------------------------------------- 1. 读取数据
    df = pd.read_csv(os.path.join(BASE, "data", "seeds.csv"))
    feature_cols = ["Area", "Perimeter", "Compactness", "Kernel_Length",
                    "Kernel_Width", "Asymmetry", "Groove_Length"]
    X_raw = df[feature_cols].to_numpy(dtype=float)
    y = df["class"].to_numpy().astype(int) - 1                       # 类别 1/2/3 → 0/1/2
    class_names = ["Kama", "Rosa", "Canadian"]
    print("种子数据集形状：", X_raw.shape, "，类别：", class_names)
    print("每类样本数：", np.bincount(y).tolist())

    X = standardize(X_raw)                               # 标准化后再聚类

    # ---------------------------------------- 2. 肘部法 + 轮廓系数选择 K
    print("\n不同 K 的聚类效果：")
    ks, sse, sil = choose_k(X)

    fig, ax1 = plt.subplots(figsize=(8.5, 5))
    ax1.plot(ks, sse, "o-", color="#2c7fb8", label="SSE（簇内误差平方和）")
    ax1.set_xlabel("簇数 K")
    ax1.set_ylabel("SSE", color="#2c7fb8")
    ax1.tick_params(axis="y", labelcolor="#2c7fb8")
    ax1.axvline(3, color="gray", ls="--", lw=1)
    ax2 = ax1.twinx()
    ax2.plot(ks, sil, "s--", color="#e6550d", label="轮廓系数")
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

    # ---------------------------------------------------- 3. 用 K=3 聚类
    km = KMeans(n_clusters=3, n_init=10, random_state=42).fit(X)
    sil_k3 = silhouette_score(X, km.labels_)
    print("\nK=3 聚类结果：")
    print("  SSE =", round(km.inertia_, 4))
    print("  轮廓系数 =", round(sil_k3, 4))
    print("  最优一次实际迭代轮数 =", km.n_iter_)
    print("  各簇样本数 =", np.bincount(km.labels_).tolist())

    # ------------------------------- 4. 与真实品种对比（把簇编号对齐到类别）
    y_aligned, mapping = align_labels(y, km.labels_, 3)
    acc = float(np.mean(y_aligned == y))
    ari = adjusted_rand_score(y, km.labels_)
    nmi = normalized_mutual_info_score(y, km.labels_)
    print("\n簇编号 → 真实品种：", {f"簇{k}": class_names[v] for k, v in sorted(mapping.items())})
    print("  聚类准确率 =", round(acc, 4))
    print("  ARI（调整兰德指数）=", round(ari, 4))
    print("  NMI（标准化互信息）=", round(nmi, 4))
    # ------------------------------------------------ 5. 可视化：PCA 二维
    X_pca = PCA(n_components=2, random_state=42).fit_transform(X)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, labels, title, is_true in [
        (axes[0], km.labels_, "K-Means 聚类结果（簇编号）", False),
        (axes[1], y, "真实小麦品种", True),
    ]:
        for c in range(3):
            m = labels == c
            name = class_names[c] if is_true else f"簇 {c}"
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
    cm = confusion_matrix(y, y_aligned)
    disp = ConfusionMatrixDisplay(cm, display_labels=class_names)
    disp.plot(cmap="Blues")
    plt.title("种子数据集：聚类结果 vs 真实品种 混淆矩阵")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task2_种子数据集_混淆矩阵.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("混淆矩阵图已保存：", out)
    print("混淆矩阵（行=真实品种，列=聚类结果）：\n", cm)


if __name__ == "__main__":
    main()
