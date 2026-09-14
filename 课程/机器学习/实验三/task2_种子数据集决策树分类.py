# -*- coding: utf-8 -*-
"""
实验三 任务2：用纯python代码对种子数据集进行分类

数据集（提供）：data/seeds_dataset.txt —— UCI 小麦种子数据集（Seeds）
    - 样本数：210；特征数：7（面积、周长、紧密度、籽粒长度、籽粒宽度、不对称系数、腹沟长度）；
    - 类别数：3（Kama / Rosa / Canadian 三个小麦品种，每类 70 个样本）；
    - 文件为制表符分隔，前 7 列是连续特征，最后一列是品种编号 1/2/3。

用到的纯python代码（均未改动）：
    代码2/id3.py  ：只能处理离散特征（信息增益）。种子特征是连续的，所以要先把特征离散化；
    代码2/c45.py  ：能直接处理连续特征（用信息增益率，连续特征枚举中点做二分分裂）；
    代码2/cart.py ：CART 分类树（用 Gini 系数，连续特征二分）；
    代码1/分类回归树/cart_classification.py：面向对象写法的 CART 分类树。

流程：
    1. 读取种子数据集，按类别分层划分训练集 / 测试集（7:3）；
    2. 分别用上述 4 种纯 python 实现建树并预测，再和 sklearn 对比；
    3. 指标：训练/测试准确率、宏平均 F1；并做 5 折交叉验证；
    4. 可视化：各方法指标对比、决策树、混淆矩阵、特征重要性、预剪枝曲线、PCA 分类结果。

运行：python task2_种子数据集决策树分类.py
"""
import os
import sys
import io
import contextlib
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (accuracy_score, f1_score, confusion_matrix,
                             ConfusionMatrixDisplay)
from sklearn.decomposition import PCA

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
CODE_DIR = os.path.join(BASE, "决策树")
os.makedirs(IMG_DIR, exist_ok=True)

# 把三份纯python代码加入搜索路径，直接复用其中的函数
sys.path.insert(0, os.path.join(CODE_DIR, "纯python代码2"))
sys.path.insert(0, os.path.join(CODE_DIR, "纯python代码1", "分类回归树"))
# 兼容补丁：现有代码基于旧版 NumPy，np.mat / np.int / np.object 在 NumPy 2.x 中已被移除
if not hasattr(np, "mat"):
    np.mat = np.asmatrix
np.int, np.object = int, object

import id3                       # noqa: E402  代码2：ID3
import c45                       # noqa: E402  代码2：C4.5
import cart                      # noqa: E402  代码2：CART
from cart_classification import CartClassificationTree   # noqa: E402  代码1：CART 分类树

import dt_utils                  # noqa: E402  本实验公共工具

FEATURE_NAMES = ["area", "perimeter", "compactness", "kernel_length",
                 "kernel_width", "asymmetry", "groove"]
CLASS_NAMES = ["Kama", "Rosa", "Canadian"]


@contextlib.contextmanager
def quiet():
    """临时屏蔽现有代码里的调试打印（不改动源代码）"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield buf


def load_seeds(path):
    """读取种子数据集：前 7 列是特征，最后一列是类别 1/2/3（转成 0/1/2）"""
    data = np.loadtxt(path)
    X = data[:, :7]
    y = data[:, 7].astype(int) - 1
    return X, y


def to_teacher_mat(X, y):
    """把数值矩阵转成现有代码需要的 np.mat（元素是字符串，最后一列是类别 1/2/3）"""
    rows = []
    for i in range(X.shape[0]):
        rows.append([repr(float(v)) for v in X[i]] + [str(int(y[i]) + 1)])
    return np.mat(rows)


def teacher_predict(tree, feature_list, mat, classify_fn, fallback=None):
    """用代码里的 classify 函数逐行预测，返回 (整数标签数组, 回退次数)

    id3.classify 在“测试样本的某个取值没在该节点的训练数据里出现过”时会返回 None，
    这类情况用一个默认类别（训练集多数类）兜底，并统计回退次数。
    """
    preds = []
    n_fallback = 0
    for i in range(mat.shape[0]):
        pred = classify_fn(tree, feature_list, mat[i, :-1])
        if pred is None:
            n_fallback += 1
            preds.append(fallback)
        else:
            preds.append(int(float(pred)) - 1)
    return np.array(preds), n_fallback


def discretize_by_quantile(X_train, X_test, n_bins=3):
    """按训练集的分位数把连续特征离散化（ID3 只能处理离散特征）"""
    edges = np.quantile(X_train, np.linspace(0, 1, n_bins + 1)[1:-1], axis=0)

    def transform(X):
        Xb = np.zeros(X.shape, dtype=int)
        for j in range(X.shape[1]):
            Xb[:, j] = np.searchsorted(edges[:, j], X[:, j], side="right")
        return Xb

    return transform(X_train), transform(X_test), edges


def metrics_row(y_true, y_pred):
    return accuracy_score(y_true, y_pred), f1_score(y_true, y_pred, average="macro")


def main():
    X, y = load_seeds(os.path.join(BASE, "data", "seeds_dataset.txt"))
    print("=" * 78)
    print("实验三 任务2：用纯python代码对种子数据集进行分类")
    print("=" * 78)
    print("数据规模：%d 个样本，%d 个特征，%d 个类别；每类样本数：%s"
          % (X.shape[0], X.shape[1], len(CLASS_NAMES), np.bincount(y).tolist()))

    # 按类别分层划分训练集 / 测试集
    idx = np.arange(X.shape[0])
    idx_train, idx_test, y_train, y_test = train_test_split(
        idx, y, test_size=0.3, random_state=42, stratify=y)
    X_train, X_test = X[idx_train], X[idx_test]
    # ID3 遇到训练时没见过的取值会返回 None，用训练集多数类兜底
    major = int(np.bincount(y_train).argmax())

    results = {}

    # ---------------- 1. 代码2：ID3（先把连续特征离散化） ----------------
    Xb_train, Xb_test, _ = discretize_by_quantile(X_train, X_test, n_bins=3)
    mat_train = to_teacher_mat(Xb_train, y_train)     # 离散化后当离散特征用
    mat_test = to_teacher_mat(Xb_test, y_test)
    tree_id3 = id3.build_id3_tree(mat_train, FEATURE_NAMES)
    pred_tr, fb1 = teacher_predict(tree_id3, FEATURE_NAMES, mat_train, id3.classify, fallback=major)
    pred_te, fb2 = teacher_predict(tree_id3, FEATURE_NAMES, mat_test, id3.classify, fallback=major)
    results["ID3（离散化）"] = {
        "模型": tree_id3, "kind": "id3",
        "训练预测": pred_tr, "测试预测": pred_te,
    }
    if fb1 + fb2:
        print("  [ID3] 提示：训练集与测试集中共有 %d 个样本的取值在该节点未出现过，已用多数类兜底。"
              % (fb1 + fb2))

    # ---------------- 2. 代码2：C4.5（直接处理连续特征） ----------------
    mat_train = to_teacher_mat(X_train, y_train)
    mat_test = to_teacher_mat(X_test, y_test)
    with quiet():
        tree_c45 = c45.build_c45_tree(mat_train, FEATURE_NAMES)
    pred_tr, fb1 = teacher_predict(tree_c45, FEATURE_NAMES, mat_train, c45.classify, fallback=major)
    pred_te, fb2 = teacher_predict(tree_c45, FEATURE_NAMES, mat_test, c45.classify, fallback=major)
    results["C4.5（连续）"] = {
        "模型": tree_c45, "kind": "c45",
        "训练预测": pred_tr, "测试预测": pred_te,
    }

    # ---------------- 3. 代码2：CART（连续特征 + Gini） ----------------
    with quiet():
        tree_cart2 = cart.build_cart_tree(mat_train, FEATURE_NAMES)
    pred_tr, _ = teacher_predict(tree_cart2, FEATURE_NAMES, mat_train, cart.classify, fallback=major)
    pred_te, _ = teacher_predict(tree_cart2, FEATURE_NAMES, mat_test, cart.classify, fallback=major)
    results["CART（代码2）"] = {
        "模型": tree_cart2, "kind": "cart",
        "训练预测": pred_tr, "测试预测": pred_te,
    }

    # ---------------- 4. 代码1：CART 分类树（面向对象） ----------------
    cart1 = CartClassificationTree(gini_threshold=0.0, gini_dec_threshold=0.0,
                                   min_samples_split=2)
    cart1.train(X_train, y_train)
    results["CART（代码1）"] = {
        "模型": cart1, "kind": "cart1",
        "训练预测": cart1.predict(X_train).astype(int),
        "测试预测": cart1.predict(X_test).astype(int),
    }

    # ---------------- 5. sklearn 决策树 ----------------
    sk_tree = DecisionTreeClassifier(criterion="entropy", random_state=42)
    sk_tree.fit(X_train, y_train)
    results["sklearn（熵）"] = {
        "模型": sk_tree, "kind": "sklearn",
        "训练预测": sk_tree.predict(X_train),
        "测试预测": sk_tree.predict(X_test),
    }

    # ---------------- 汇总指标 ----------------
    print()
    print("%-16s %14s %14s %14s" % ("方法", "训练准确率", "测试准确率", "测试宏F1"))
    summary = {}
    for name, res in results.items():
        tr_acc, tr_f1 = metrics_row(y_train, res["训练预测"])
        te_acc, te_f1 = metrics_row(y_test, res["测试预测"])
        summary[name] = (tr_acc, te_acc, te_f1)
        print("%-16s %13.2f%% %13.2f%% %14.3f" % (name, tr_acc * 100, te_acc * 100, te_f1))

    # 5 折交叉验证（用 sklearn 的模型做参考）
    cv = cross_val_score(DecisionTreeClassifier(criterion="entropy", random_state=42),
                         X, y, cv=5)
    print()
    print("sklearn（熵）5 折交叉验证准确率：%s，平均 %.2f%%"
          % (" ".join("%.3f" % v for v in cv), cv.mean() * 100))
    print("说明：ID3 需要先把连续特征离散化，离散化会损失信息，所以通常不如能直接处理连续的 C4.5/CART；")
    print("      现有代码在训练集上容易长成完全树（训练准确率 100%），测试准确率更能反映泛化能力。")

    # ---------------- 可视化 ----------------
    plot_metric_comparison(summary)
    plot_trees(results, X_train, y_train)
    plot_confusion(sk_tree, X_test, y_test)
    plot_importance(sk_tree)
    plot_pruning_curve(X_train, y_train, X_test, y_test)
    plot_pca(X, y, sk_tree)

    print()
    print("任务2 运行完毕，所有图片都在：", IMG_DIR)


def plot_metric_comparison(summary):
    """各方法的训练/测试准确率与测试宏 F1 对比柱状图"""
    names = list(summary.keys())
    x = np.arange(len(names))
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    w = 0.38
    axes[0].bar(x - w / 2, [summary[n][0] for n in names], width=w, label="训练准确率", color="#3498db")
    axes[0].bar(x + w / 2, [summary[n][1] for n in names], width=w, label="测试准确率", color="#e67e22")
    for i, n in enumerate(names):
        axes[0].text(i - w / 2, summary[n][0] + 0.01, "%.2f" % summary[n][0], ha="center", fontsize=8)
        axes[0].text(i + w / 2, summary[n][1] + 0.01, "%.2f" % summary[n][1], ha="center", fontsize=8)
    axes[0].set_xticks(x); axes[0].set_xticklabels(names, rotation=15)
    axes[0].set_ylim(0, 1.32); axes[0].set_ylabel("准确率")
    axes[0].set_title("准确率对比", fontsize=11)
    axes[0].legend(loc="upper center", ncol=2, fontsize=9)
    axes[0].grid(alpha=0.3, axis="y")

    axes[1].bar(x, [summary[n][2] for n in names], color="#8e44ad", width=0.5)
    for i, n in enumerate(names):
        axes[1].text(i, summary[n][2] + 0.012, "%.3f" % summary[n][2], ha="center", fontsize=9)
    axes[1].set_xticks(x); axes[1].set_xticklabels(names, rotation=15)
    axes[1].set_ylim(0, 1.12); axes[1].set_ylabel("宏平均 F1")
    axes[1].set_title("测试集宏平均 F1", fontsize=11); axes[1].grid(alpha=0.3, axis="y")
    fig.suptitle("种子数据集：纯 python 决策树与 sklearn 对比", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(IMG_DIR, "task2_种子数据集_各方法指标对比.png")
    fig.savefig(out, dpi=150); plt.close(fig)
    print("已保存：", out)


def plot_trees(results, X_train, y_train):
    """绘制 C4.5 / CART 的字典树，以及 sklearn 决策树"""
    depth, leaves, inner = dt_utils.tree_stats(results["C4.5（连续）"]["模型"])
    print("[C4.5] 树：深度 = %d，叶子数 = %d，内部节点数 = %d" % (depth, leaves, inner))
    png = os.path.join(IMG_DIR, "task2_种子数据集_C45决策树.png")
    dt_utils.plot_dict_tree(results["C4.5（连续）"]["模型"], png,
                            "C4.5 决策树（种子数据集）")
    with open(os.path.join(IMG_DIR, "task2_种子数据集_C45决策树.dot"), "w", encoding="utf-8") as f:
        f.write(dt_utils.dict_tree_to_dot(results["C4.5（连续）"]["模型"]))
    print("已保存：", png)

    depth, leaves, inner = dt_utils.tree_stats(results["CART（代码2）"]["模型"])
    print("[CART-代码2] 树：深度 = %d，叶子数 = %d，内部节点数 = %d" % (depth, leaves, inner))
    png = os.path.join(IMG_DIR, "task2_种子数据集_CART决策树.png")
    dt_utils.plot_dict_tree(results["CART（代码2）"]["模型"], png,
                            "CART 决策树（种子数据集）")
    print("已保存：", png)

    sk = results["sklearn（熵）"]["模型"]
    print("[sklearn] 树：深度 = %d，叶子数 = %d" % (sk.get_depth(), sk.get_n_leaves()))
    png = os.path.join(IMG_DIR, "task2_种子数据集_sklearn决策树.png")
    dt_utils.plot_sklearn_tree(sk, FEATURE_NAMES, CLASS_NAMES, png,
                               "sklearn 决策树（criterion=entropy，种子数据集）")
    print("已保存：", png)


def plot_confusion(sk_tree, X_test, y_test):
    y_pred = sk_tree.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    ConfusionMatrixDisplay(cm, display_labels=CLASS_NAMES).plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title("sklearn 决策树：测试集混淆矩阵", fontsize=12)
    fig.tight_layout()
    out = os.path.join(IMG_DIR, "task2_种子数据集_混淆矩阵.png")
    fig.savefig(out, dpi=150); plt.close(fig)
    print("已保存：", out)


def plot_importance(sk_tree):
    imp = sk_tree.feature_importances_
    order = np.argsort(imp)[::-1]
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ax.bar(range(len(imp)), imp[order], color="#16a085", width=0.6)
    ax.set_xticks(range(len(imp)))
    ax.set_xticklabels([FEATURE_NAMES[i] for i in order], rotation=20)
    ax.set_ylabel("特征重要性")
    ax.set_title("sklearn 决策树的特征重要性（种子数据集）", fontsize=12)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    out = os.path.join(IMG_DIR, "task2_种子数据集_特征重要性.png")
    fig.savefig(out, dpi=150); plt.close(fig)
    print("已保存：", out)


def plot_pruning_curve(X_train, y_train, X_test, y_test):
    """预剪枝：限制最大深度 max_depth，观察训练/测试准确率与交叉验证准确率"""
    depths = list(range(1, 13))
    train_acc, test_acc, cv_acc = [], [], []
    for d in depths:
        clf = DecisionTreeClassifier(criterion="entropy", max_depth=d, random_state=42)
        clf.fit(X_train, y_train)
        train_acc.append(clf.score(X_train, y_train))
        test_acc.append(clf.score(X_test, y_test))
        cv_acc.append(cross_val_score(DecisionTreeClassifier(criterion="entropy", max_depth=d,
                                                             random_state=42),
                                      X_train, y_train, cv=5).mean())
    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    ax.plot(depths, train_acc, "o-", label="训练准确率", color="#3498db")
    ax.plot(depths, test_acc, "s-", label="测试准确率", color="#e67e22")
    ax.plot(depths, cv_acc, "^--", label="5 折交叉验证准确率", color="#27ae60")
    best = depths[int(np.argmax(cv_acc))]
    ax.axvline(best, color="#c0392b", ls=":", alpha=0.8)
    ax.text(best + 0.1, 0.62, "交叉验证最优深度 = %d" % best, color="#c0392b", fontsize=10)
    ax.set_xlabel("决策树最大深度 max_depth"); ax.set_ylabel("准确率")
    ax.set_title("预剪枝：深度对决策树泛化能力的影响（种子数据集）", fontsize=12)
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    out = os.path.join(IMG_DIR, "task2_种子数据集_预剪枝_深度与准确率.png")
    fig.savefig(out, dpi=150); plt.close(fig)
    print("已保存：", out, "；交叉验证最优深度 =", best)


def plot_pca(X, y, sk_tree):
    """PCA 降到 2 维，展示真实类别与决策树预测的分布"""
    pca = PCA(n_components=2, random_state=42)
    X2 = pca.fit_transform(X)
    y_pred = sk_tree.predict(X)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    colors = ["#e74c3c", "#3498db", "#27ae60"]
    for k, name in enumerate(CLASS_NAMES):
        axes[0].scatter(X2[y == k, 0], X2[y == k, 1], s=22, c=colors[k], label=name, alpha=0.8)
        axes[1].scatter(X2[y_pred == k, 0], X2[y_pred == k, 1], s=22, c=colors[k], label=name, alpha=0.8)
    axes[0].set_title("真实类别（PCA 2 维）", fontsize=11)
    axes[1].set_title("决策树预测类别（PCA 2 维）", fontsize=11)
    for ax in axes:
        ax.set_xlabel("主成分 1"); ax.set_ylabel("主成分 2")
        ax.legend(fontsize=9); ax.grid(alpha=0.3)
    fig.suptitle("种子数据集：PCA 降维后的分类结果", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(IMG_DIR, "task2_种子数据集_PCA分类结果.png")
    fig.savefig(out, dpi=150); plt.close(fig)
    print("已保存：", out)


if __name__ == "__main__":
    main()
