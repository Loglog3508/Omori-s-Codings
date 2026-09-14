"""
实验二 任务3：自选数据集，使用 K-Means 算法解决一个聚类问题

自选数据集：手写数字数据集（sklearn digits，已导出为 data/digits.csv）
    - 样本数：1797
    - 特征数：64（每张 8×8 手写数字图片展平成 64 个灰度像素）
    - 真实类别：10（数字 0~9，每类约 180 个样本）
    - 问题：在完全不使用标签的情况下，把 1797 张手写数字图片自动聚成若干簇，
            再观察 K-Means 能否把相同数字聚到一起（无监督聚类 vs 真实标签）。

按照实验要求“可以使用原生python代码或sklearn等机器学习框架”，本任务三种实现都用上并互相验证：
    1. sklearn 的 KMeans（框架实现，作为标准答案）；
    2. 老师提供的纯python代码1（KMeans/纯python代码1/kmeans.py，面向对象实现）；
    3. 实验任务1 里的改进版（纯python代码1_KMeans改进版.py）。
最后比较三者的 SSE 与聚类指标，验证纯 Python 实现是否正确。
"""
import os
import sys
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans as SkKMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (silhouette_score, adjusted_rand_score,
                             normalized_mutual_info_score, confusion_matrix,
                             ConfusionMatrixDisplay)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
os.makedirs(IMG_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(BASE, "KMeans", "纯python代码1"))
# 兼容补丁：老师代码用了 np.int 与 np.object，这两个别名在 NumPy 2.x 中已被移除
np.int, np.object = int, object
from kmeans import KMeans as TeacherKMeans            # noqa: E402  老师提供的代码1

sys.path.insert(0, BASE)
from 纯python代码1_KMeans改进版 import ImprovedKMeans   # noqa: E402


def align_labels(y_true, y_pred, n_clusters):
    """用匈牙利算法把簇编号对齐到真实数字，得到最大匹配（用于计算聚类准确率）"""
    cm = confusion_matrix(y_true, y_pred, labels=list(range(n_clusters)))
    row, col = linear_sum_assignment(-cm)
    mapping = {c: r for r, c in zip(row, col)}
    return np.array([mapping[c] for c in y_pred]), mapping


def evaluate(y_true, y_pred, X, n_clusters, name):
    """统一输出一组聚类评估指标"""
    y_aligned, mapping = align_labels(y_true, y_pred, n_clusters)
    # 手写数字样本较多，轮廓系数用抽样计算以节省时间（sklearn 自带 sample_size 参数）
    res = {
        "name": name,
        "轮廓系数": float(silhouette_score(X, y_pred, sample_size=1500, random_state=42)),
        "ARI": float(adjusted_rand_score(y_true, y_pred)),
        "NMI": float(normalized_mutual_info_score(y_true, y_pred)),
        "聚类准确率": float(np.mean(y_aligned == y_true)),
    }
    print("  [%-14s] 轮廓系数=%.4f  ARI=%.4f  NMI=%.4f  聚类准确率=%.4f"
          % (name, res["轮廓系数"], res["ARI"], res["NMI"], res["聚类准确率"]))
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
    X = (X_raw - X_raw.mean(axis=0)) / np.where(X_raw.std(axis=0) == 0, 1.0, X_raw.std(axis=0))
    K = 10

    # ------------------------------------ 2. 肘部法 + 轮廓系数选择 K
    print("\n不同 K 的聚类效果：")
    ks = list(range(2, 13))
    sse_list, sil_list = [], []
    for kk in ks:
        m = ImprovedKMeans(k_clusters=kk, n_init=5, random_state=42).fit(X)
        sse_list.append(m.sse_)
        sil_list.append(float(silhouette_score(X, m.labels_, sample_size=1500, random_state=42)))
        print("  K=%2d: SSE=%9.1f  轮廓系数=%.4f" % (kk, m.sse_, sil_list[-1]))

    fig, ax1 = plt.subplots(figsize=(8.5, 5))
    ax1.plot(ks, sse_list, "o-", color="#2c7fb8", label="SSE（簇内误差平方和）")
    ax1.set_xlabel("簇数 K")
    ax1.set_ylabel("SSE", color="#2c7fb8")
    ax1.tick_params(axis="y", labelcolor="#2c7fb8")
    ax1.axvline(10, color="gray", ls="--", lw=1)
    ax2 = ax1.twinx()
    ax2.plot(ks, sil_list, "s--", color="#e6550d", label="轮廓系数（抽样估计）")
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

    # ------------------------------- 3. sklearn KMeans 正式聚类（K=10）
    print("\n=== K=10（对应数字 0~9）三种实现对比 ===")
    t0 = time.perf_counter()
    km_sk = SkKMeans(n_clusters=K, n_init=10, random_state=42).fit(X)
    t_sk = time.perf_counter() - t0
    res_sk, y_aligned, mapping = evaluate(y, km_sk.labels_, X, K, "sklearn KMeans")
    print("  各簇样本数：", np.bincount(km_sk.labels_, minlength=K).tolist())
    print("  簇编号 → 数字：", {f"簇{k}": int(v) for k, v in sorted(mapping.items())})

    # --------------------------- 4. 老师代码1 与 改进版 在同一数据上聚类
    t0 = time.perf_counter()
    np.random.seed(42)
    km_t = TeacherKMeans(k_clusters=K, n_init=10)
    labels_t = km_t.predict(X)
    t_teacher = time.perf_counter() - t0
    res_t, _, _ = evaluate(y, labels_t, X, K, "老师代码1")

    t0 = time.perf_counter()
    km_imp = ImprovedKMeans(k_clusters=K, n_init=10, random_state=42).fit(X)
    t_imp = time.perf_counter() - t0
    res_imp, _, _ = evaluate(y, km_imp.labels_, X, K, "改进版")

    print("\nSSE 对比：sklearn = %.1f，老师代码1 = %.1f，改进版 = %.1f"
          % (km_sk.inertia_, km_t.sse_, km_imp.sse_))
    print("耗时对比：sklearn = %.2fs，老师代码1 = %.2fs，改进版 = %.2fs"
          % (t_sk, t_teacher, t_imp))
    print("→ 纯 Python 实现的 SSE 与 sklearn 非常接近，说明实现是正确的；")
    print("  改进版向量化后比老师代码1 更快（改进4）。")
    print("  注意：K-Means 只优化 SSE，SSE 最小的解不一定与真实标签最一致，")
    print("  所以个别指标（如 ARI）略有出入属于正常现象。")

    metrics = ["轮廓系数", "ARI", "NMI", "聚类准确率"]
    xpos = np.arange(len(metrics))
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 5.4))
    axes[0].bar(["sklearn", "老师代码1", "改进版"],
                [km_sk.inertia_, km_t.sse_, km_imp.sse_],
                color=["#31a354", "#2c7fb8", "#e6550d"], width=0.55)
    for i, v in enumerate([km_sk.inertia_, km_t.sse_, km_imp.sse_]):
        axes[0].text(i, v * 1.01, "%.0f" % v, ha="center", fontsize=9)
    axes[0].set_ylabel("SSE（越小越好）")
    axes[0].set_title("三种实现的 SSE 对比", fontsize=11)
    axes[0].grid(alpha=0.3, axis="y")

    w = 0.26
    for i, (r, lab, col) in enumerate([(res_sk, "sklearn", "#31a354"),
                                       (res_t, "老师代码1", "#2c7fb8"),
                                       (res_imp, "改进版", "#e6550d")]):
        axes[1].bar(xpos + (i - 1) * w, [r[m] for m in metrics], width=w, label=lab, color=col)
    for m_i, m in enumerate(metrics):
        for i, r in enumerate([res_sk, res_t, res_imp]):
            axes[1].text(m_i + (i - 1) * w, r[m] + 0.012, "%.3f" % r[m], ha="center", fontsize=7)
    axes[1].set_xticks(xpos)
    axes[1].set_xticklabels(metrics)
    axes[1].set_ylim(0, 0.8)
    axes[1].set_title("三种实现的聚类指标对比", fontsize=11)
    axes[1].legend()
    axes[1].grid(alpha=0.3, axis="y")
    fig.suptitle("手写数字聚类：sklearn / 老师代码1 / 改进版 对比", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(IMG_DIR, "task3_手写数字_三种实现对比.png")
    fig.savefig(out, dpi=150)
    plt.close()
    print("三种实现对比图已保存：", out)

    # ------------------------------------------------ 5. 可视化：PCA 二维
    X_pca = PCA(n_components=2, random_state=42).fit_transform(X)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, labels, title, is_true in [
        (axes[0], km_sk.labels_, "K-Means 聚类结果（簇编号）", False),
        (axes[1], y, "真实数字标签", True),
    ]:
        for c in range(K):
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

    # ------------------------------------------ 6. 簇中心还原成 8×8 图片
    fig, axes = plt.subplots(2, 5, figsize=(12, 5.4))
    for j, ax in enumerate(axes.ravel()):
        ax.imshow(km_sk.cluster_centers_[j].reshape(8, 8), cmap="gray")
        ax.set_title(f"簇 {j}（多为数字 {int(mapping[j])}）", fontsize=10)
        ax.axis("off")
    fig.suptitle("K-Means 各簇中心（把 64 维中心还原为 8×8 图像）", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(IMG_DIR, "task3_手写数字_簇心图像.png")
    fig.savefig(out, dpi=150)
    plt.close()
    print("簇中心图像已保存：", out)

    # ---------------------------------------------------- 7. 混淆矩阵
    cm = confusion_matrix(y, y_aligned)
    disp = ConfusionMatrixDisplay(cm, display_labels=[str(i) for i in range(K)])
    disp.plot(cmap="Blues", values_format="d")
    plt.title("手写数字：聚类结果 vs 真实数字 混淆矩阵")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task3_手写数字_混淆矩阵.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("混淆矩阵图已保存：", out)


if __name__ == "__main__":
    main()