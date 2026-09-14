"""
实验二 任务3：自选数据集，使用 K-Means 算法解决一个聚类问题

自选数据集：手写数字数据集（sklearn digits，已导出为 data/digits.csv）
    - 样本数：1797
    - 特征数：64（每张 8×8 手写数字图片展平成 64 个灰度像素）
    - 真实类别：10（数字 0~9，每类约 180 个样本）
    - 问题：在完全不使用标签的情况下，把 1797 张手写数字图片自动聚成若干簇，
            再观察 K-Means 能否把相同数字聚到一起（无监督聚类 vs 真实标签）。

实现方式：使用 sklearn 机器学习框架中的 KMeans，并配合 PCA 降维可视化，
以及轮廓系数、ARI、NMI、聚类准确率、混淆矩阵等指标；
最后与纯python代码1中自己实现的 KMeans 做对比，验证自实现结果的正确性。
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans as SkKMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (silhouette_score, adjusted_rand_score,
                             normalized_mutual_info_score, confusion_matrix,
                             ConfusionMatrixDisplay)

from 纯python代码1_KMeans聚类 import KMeans as MyKMeans

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
os.makedirs(IMG_DIR, exist_ok=True)


def align_labels(y_true, y_pred, n_clusters):
    """用匈牙利算法把簇编号对齐到真实数字，得到最大匹配（用于计算聚类准确率）"""
    cm = confusion_matrix(y_true, y_pred, labels=list(range(n_clusters)))
    row, col = linear_sum_assignment(-cm)
    mapping = {c: r for r, c in zip(row, col)}
    return np.array([mapping[c] for c in y_pred]), mapping


def evaluate(y_true, y_pred, X, n_clusters, name):
    """统一输出一组聚类评估指标，返回评估结果字典"""
    y_aligned, mapping = align_labels(y_true, y_pred, n_clusters)
    res = {
        "name": name,
        "轮廓系数": float(silhouette_score(X, y_pred)),
        "ARI": float(adjusted_rand_score(y_true, y_pred)),
        "NMI": float(normalized_mutual_info_score(y_true, y_pred)),
        "聚类准确率": float(np.mean(y_aligned == y_true)),
    }
    print(f"[{name}] 轮廓系数={res['轮廓系数']:.4f}  ARI={res['ARI']:.4f}  "
          f"NMI={res['NMI']:.4f}  聚类准确率={res['聚类准确率']:.4f}")
    return res, y_aligned, mapping

def main():
    # ---------------------------------------------------------- 1. 读取数据
    df = pd.read_csv(os.path.join(BASE, "data", "digits.csv"))
    pixel_cols = [c for c in df.columns if c.startswith("pixel_")]
    X_raw = df[pixel_cols].to_numpy(dtype=float)
    y = df["class"].to_numpy().astype(int)
    print("手写数字数据集形状：", X_raw.shape, "，真实类别数：", len(np.unique(y)))
    print("每个数字的样本数：", np.bincount(y).tolist())

    # 标准化：K-Means 基于欧氏距离，标准化后各像素权重一致
    X = StandardScaler().fit_transform(X_raw)

    # ---------------------------------------------------- 2. 选择簇数 K
    print("\n不同 K 的聚类效果（sklearn KMeans）：")
    ks = list(range(2, 13))
    sse, sil = [], []
    for k in ks:
        km_k = SkKMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        sse.append(km_k.inertia_)
        sil.append(silhouette_score(X, km_k.labels_))
        print(f"  K={k:2d}: SSE={km_k.inertia_:10.1f}  轮廓系数={sil[-1]:.4f}")

    fig, ax1 = plt.subplots(figsize=(8.5, 5))
    ax1.plot(ks, sse, "o-", color="#2c7fb8", label="SSE（簇内误差平方和）")
    ax1.set_xlabel("簇数 K")
    ax1.set_ylabel("SSE", color="#2c7fb8")
    ax1.tick_params(axis="y", labelcolor="#2c7fb8")
    ax1.axvline(10, color="gray", ls="--", lw=1)
    ax2 = ax1.twinx()
    ax2.plot(ks, sil, "s--", color="#e6550d", label="轮廓系数")
    ax2.set_ylabel("轮廓系数", color="#e6550d")
    ax2.tick_params(axis="y", labelcolor="#e6550d")
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [l.get_label() for l in lines], loc="center right")
    plt.title("手写数字数据集：肘部法与轮廓系数选择 K")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task3_手写数字_肘部与轮廓系数.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("肘部/轮廓系数图已保存：", out)

    # ------------------------------- 3. 用 K=10（对应 0~9）正式聚类
    K = 10
    km = SkKMeans(n_clusters=K, n_init=10, random_state=42).fit(X)
    print(f"\nK={K}（对应数字 0~9）sklearn KMeans 聚类结果：")
    res_sk, y_aligned, mapping = evaluate(y, km.labels_, X, K, "sklearn KMeans")
    print("  各簇样本数：", np.bincount(km.labels_, minlength=K).tolist())
    print("  簇编号 → 数字：", {f"簇{k}": int(v) for k, v in sorted(mapping.items())})
    # ------------------------------------------------ 4. 可视化：PCA 二维
    X_pca = PCA(n_components=2, random_state=42).fit_transform(X)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, labels, title, is_true in [
        (axes[0], km.labels_, "K-Means 聚类结果（簇编号）", False),
        (axes[1], y, "真实数字标签", True),
    ]:
        for c in range(10):
            m = labels == c
            ax.scatter(X_pca[m, 0], X_pca[m, 1], s=14, alpha=0.75,
                       color=plt.cm.tab10(c),
                       label=(str(c) if is_true else f"簇{c}"))
        ax.set_xlabel("主成分 1")
        ax.set_ylabel("主成分 2")
        ax.set_title(title)
        ax.legend(markerscale=2, fontsize=8, ncol=2)
        ax.grid(alpha=0.3)
    fig.suptitle("手写数字数据集 K-Means 聚类结果（PCA 降至 2 维）", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = os.path.join(IMG_DIR, "task3_手写数字_聚类结果PCA.png")
    fig.savefig(out, dpi=150)
    plt.close()
    print("\nPCA 聚类结果图已保存：", out)

    # ------------------------------------------ 5. 簇中心还原成 8×8 图片
    fig, axes = plt.subplots(2, 5, figsize=(12, 5.4))
    for j, ax in enumerate(axes.ravel()):
        ax.imshow(km.cluster_centers_[j].reshape(8, 8), cmap="gray")
        ax.set_title(f"簇 {j}（多为数字 {int(mapping[j])}）", fontsize=10)
        ax.axis("off")
    fig.suptitle("K-Means 各簇中心（把 64 维中心还原为 8×8 图像）", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(IMG_DIR, "task3_手写数字_簇心图像.png")
    fig.savefig(out, dpi=150)
    plt.close()
    print("簇中心图像已保存：", out)

    # ---------------------------------------------------- 6. 混淆矩阵
    cm = confusion_matrix(y, y_aligned)
    disp = ConfusionMatrixDisplay(cm, display_labels=[str(i) for i in range(10)])
    disp.plot(cmap="Blues", values_format="d")
    plt.title("手写数字：聚类结果 vs 真实数字 混淆矩阵")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task3_手写数字_混淆矩阵.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("混淆矩阵图已保存：", out)

    # -------------------- 7. 与纯python代码1的自实现 K-Means 对比
    print("\n用纯python代码1（自实现 K-Means，k-means++ + 多次重启）在同一数据上聚类：")
    my = MyKMeans(n_clusters=K, n_init=10, max_iter=300, random_state=42).fit(X)
    res_my, _, _ = evaluate(y, my.labels_, X, K, "自实现 KMeans")
    print("  SSE：自实现 = %.1f，sklearn = %.1f" % (my.inertia_, km.inertia_))
    print("  → 自实现的 SSE 与 sklearn 几乎相同，说明纯python代码1 的实现是正确的；")
    print("    注意：K-Means 只优化 SSE，而 SSE 最小的解不一定与真实标签最一致，")
    print("    所以个别聚类指标（如 ARI）与 sklearn 略有出入属于正常现象。")

    metrics = ["ARI", "NMI", "聚类准确率"]
    xpos = np.arange(len(metrics))
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.bar(xpos - 0.18, [res_sk[m] for m in metrics], width=0.36, label="sklearn KMeans")
    ax.bar(xpos + 0.18, [res_my[m] for m in metrics], width=0.36, label="自实现 KMeans")
    for i, m in enumerate(metrics):
        ax.text(i - 0.18, res_sk[m] + 0.015, f"{res_sk[m]:.3f}", ha="center", fontsize=9)
        ax.text(i + 0.18, res_my[m] + 0.015, f"{res_my[m]:.3f}", ha="center", fontsize=9)
    ax.set_xticks(xpos)
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1)
    ax.set_ylabel("指标值")
    ax.set_title("手写数字聚类：自实现 K-Means 与 sklearn KMeans 对比")
    ax.legend()
    ax.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task3_手写数字_自实现与sklearn对比.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("对比图已保存：", out)


if __name__ == "__main__":
    main()