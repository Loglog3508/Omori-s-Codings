# -*- coding: utf-8 -*-
"""
实验三 任务3：自己找数据集，用决策树解决一个分类问题和回归问题

自选数据集（都是 sklearn 自带、无需联网下载）：
    分类问题：wine 葡萄酒数据集 —— 178 个样本、13 个特征、3 个类别（三个品种）；
    回归问题：diabetes 糖尿病数据集 —— 442 个样本、10 个特征，标签是一年后病情进展的连续数值。

使用的计算方式：
    1. sklearn 的决策树（分类用 DecisionTreeClassifier，回归用 DecisionTreeRegressor），
       这是本任务的主要模型，并用 5 折交叉验证挑选合适的最大深度；
    2. 纯 python CART 代码（代码1/分类回归树/cart_classification.py 与 cart_regression.py），
       在同样数据上训练，和 sklearn 对照，说明纯 python 实现也是正确的；
    3. 用 graphviz 的思路把决策树导出成 .dot 文件：sklearn 的 export_graphviz 能直接生成 DOT 文本；
       若本机安装了 Graphviz 程序，脚本会顺带把 .dot 渲染成图片，否则只保留 .dot 文件（不影响实验）。

运行：python task3_自选数据集_决策树分类与回归.py
"""
import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_wine, load_diabetes
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.metrics import (accuracy_score, f1_score, confusion_matrix,
                             ConfusionMatrixDisplay, mean_squared_error,
                             mean_absolute_error, r2_score)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
os.makedirs(IMG_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(BASE, "决策树", "纯python代码1", "分类回归树"))
import dt_utils
from cart_classification import CartClassificationTree   # 代码1：CART 分类树
from cart_regression import CartRegressionTree            # 代码1：CART 回归树


# ============================================================================
# 一、分类问题：wine 葡萄酒数据集
# ============================================================================
def run_classification():
    print("=" * 78)
    print("一、分类问题：wine 葡萄酒数据集（sklearn 决策树 + 纯 python CART）")
    print("=" * 78)
    data = load_wine()
    X, y, names = data.data, data.target, list(data.feature_names)
    class_names = [str(t) for t in data.target_names]
    print("数据规模：%d 个样本，%d 个特征，%d 个类别（%s）"
          % (X.shape[0], X.shape[1], len(class_names), class_names))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y)

    # --- 5 折交叉验证挑选最大深度（预剪枝） ---
    depths = list(range(1, 11))
    cv_scores = [cross_val_score(DecisionTreeClassifier(max_depth=d, random_state=42),
                                 X_train, y_train, cv=5).mean() for d in depths]
    best_depth = depths[int(np.argmax(cv_scores))]
    print("5 折交叉验证最优最大深度 max_depth = %d（交叉验证准确率 %.2f%%）"
          % (best_depth, max(cv_scores) * 100))

    clf = DecisionTreeClassifier(max_depth=best_depth, random_state=42)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="macro")
    print("sklearn 决策树：训练准确率 %.2f%%，测试准确率 %.2f%%，测试宏 F1 = %.3f"
          % (clf.score(X_train, y_train) * 100, acc * 100, f1))

    # --- 纯 python CART 分类树 ---
    t0 = time.time()
    cart1 = CartClassificationTree(gini_threshold=0.0, gini_dec_threshold=0.0,
                                   min_samples_split=5)
    cart1.train(X_train, y_train)
    t_cart = time.time() - t0
    cart_pred = cart1.predict(X_test).astype(int)
    cart_train_acc = accuracy_score(y_train, cart1.predict(X_train).astype(int))
    print("纯 python CART：训练准确率 %.2f%%，测试准确率 %.2f%%，测试宏 F1 = %.3f，训练耗时 %.2f 秒"
          % (cart_train_acc * 100, accuracy_score(y_test, cart_pred) * 100,
             f1_score(y_test, cart_pred, average="macro"), t_cart))
    print("两者结果接近，说明纯 python 的 CART 实现是正确的。")

    # --- 可视化 ---
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.plot(depths, [1 - s for s in cv_scores], "o-", color="#e67e22")
    ax.axvline(best_depth, color="#c0392b", ls=":", alpha=0.8)
    ax.set_xlabel("最大深度 max_depth"); ax.set_ylabel("5 折交叉验证错误率")
    ax.set_title("wine 分类：用交叉验证选择树的深度（预剪枝）", fontsize=12)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "task3_wine_预剪枝_深度与错误率.png"), dpi=150)
    plt.close(fig)

    dt_utils.plot_sklearn_tree(clf, names, class_names,
                               os.path.join(IMG_DIR, "task3_wine_决策树.png"),
                               "wine 分类决策树（sklearn，max_depth=%d）" % best_depth)
    dot_path = dt_utils.export_sklearn_dot(clf, names, class_names,
                                           os.path.join(IMG_DIR, "task3_wine_决策树.dot"))
    render_graphviz(dot_path, os.path.join(IMG_DIR, "task3_wine_决策树_graphviz.png"))

    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    ConfusionMatrixDisplay(cm, display_labels=class_names).plot(
        ax=ax, cmap="Greens", colorbar=False)
    ax.set_title("wine 分类：测试集混淆矩阵", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "task3_wine_混淆矩阵.png"), dpi=150)
    plt.close(fig)

    imp = clf.feature_importances_
    order = np.argsort(imp)[::-1][:10]
    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    ax.bar(range(len(order)), imp[order], color="#16a085", width=0.62)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([names[i] for i in order], rotation=30, ha="right")
    ax.set_ylabel("特征重要性")
    ax.set_title("wine 分类决策树的特征重要性", fontsize=12)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "task3_wine_特征重要性.png"), dpi=150)
    plt.close(fig)
    print("wine 相关图已保存到：", IMG_DIR)

    return clf, (X, y, names)


# ============================================================================
# 二、回归问题：diabetes 糖尿病数据集
# ============================================================================
def run_regression():
    print()
    print("=" * 78)
    print("二、回归问题：diabetes 糖尿病数据集（sklearn 回归树 + 纯 python CART）")
    print("=" * 78)
    data = load_diabetes()
    X, y, names = data.data, data.target, list(data.feature_names)
    print("数据规模：%d 个样本，%d 个特征；标签取值范围 %.0f ~ %.0f（连续值）"
          % (X.shape[0], X.shape[1], y.min(), y.max()))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42)

    depths = list(range(1, 13))
    cv_r2 = [cross_val_score(DecisionTreeRegressor(max_depth=d, random_state=42),
                             X_train, y_train, cv=5, scoring="r2").mean() for d in depths]
    best_depth = depths[int(np.argmax(cv_r2))]
    print("5 折交叉验证最优最大深度 max_depth = %d（交叉验证 R2 = %.3f）"
          % (best_depth, max(cv_r2)))

    reg = DecisionTreeRegressor(max_depth=best_depth, random_state=42)
    reg.fit(X_train, y_train)
    y_pred = reg.predict(X_test)
    report_regression("sklearn 回归树", y_test, y_pred)

    # --- 纯 python CART 回归树 ---
    t0 = time.time()
    cart_reg = CartRegressionTree(mse_threshold=0.0, mse_dec_threshold=0.0,
                                  min_samples_split=20)
    cart_reg.train(X_train, y_train)
    t_cart = time.time() - t0
    cart_pred = cart_reg.predict(X_test)
    report_regression("纯 python CART 回归树", y_test, cart_pred)
    print("（纯 python 回归树训练耗时 %.2f 秒）" % t_cart)

    # --- 可视化 ---
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    ax.plot(depths, cv_r2, "o-", color="#2980b9")
    ax.axvline(best_depth, color="#c0392b", ls=":", alpha=0.8)
    ax.set_xlabel("最大深度 max_depth"); ax.set_ylabel("5 折交叉验证 R2")
    ax.set_title("diabetes 回归：用交叉验证选择树的深度", fontsize=12)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "task3_diabetes_预剪枝_深度与R2.png"), dpi=150)
    plt.close(fig)

    dt_utils.plot_sklearn_tree(reg, names, None,
                               os.path.join(IMG_DIR, "task3_diabetes_回归树.png"),
                               "diabetes 回归树（sklearn，max_depth=%d）" % best_depth)
    dot_path = dt_utils.export_sklearn_dot(reg, names, None,
                                           os.path.join(IMG_DIR, "task3_diabetes_回归树.dot"))
    render_graphviz(dot_path, os.path.join(IMG_DIR, "task3_diabetes_回归树_graphviz.png"))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    axes[0].scatter(y_test, y_pred, s=22, c="#8e44ad", alpha=0.75)
    lim = [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())]
    axes[0].plot(lim, lim, "k--", lw=1)
    axes[0].set_xlabel("真实值"); axes[0].set_ylabel("预测值")
    axes[0].set_title("预测值 vs 真实值", fontsize=11); axes[0].grid(alpha=0.3)
    residual = y_test - y_pred
    axes[1].scatter(y_pred, residual, s=22, c="#e67e22", alpha=0.75)
    axes[1].axhline(0, color="k", ls="--", lw=1)
    axes[1].set_xlabel("预测值"); axes[1].set_ylabel("残差（真实 - 预测）")
    axes[1].set_title("残差图", fontsize=11); axes[1].grid(alpha=0.3)
    fig.suptitle("diabetes 回归树：测试集预测效果", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(IMG_DIR, "task3_diabetes_预测与残差.png"), dpi=150)
    plt.close(fig)

    imp = reg.feature_importances_
    order = np.argsort(imp)[::-1]
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ax.bar(range(len(imp)), imp[order], color="#c0392b", width=0.62)
    ax.set_xticks(range(len(imp)))
    ax.set_xticklabels([names[i] for i in order], rotation=25, ha="right")
    ax.set_ylabel("特征重要性")
    ax.set_title("diabetes 回归树的特征重要性", fontsize=12)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG_DIR, "task3_diabetes_特征重要性.png"), dpi=150)
    plt.close(fig)
    print("diabetes 相关图已保存到：", IMG_DIR)

    return reg, (X, y, names)


def report_regression(title, y_true, y_pred):
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    print("%-26s MSE = %7.1f，RMSE = %5.1f，MAE = %5.1f，R2 = %.3f"
          % (title, mean_squared_error(y_true, y_pred), rmse, mae, r2))


def render_graphviz(dot_path, png_path):
    """尝试用 Graphviz 渲染 .dot；没装 Graphviz 就只保留 .dot 文件"""
    if dt_utils.try_render_dot(dot_path, png_path):
        print("已用 Graphviz 渲染：", png_path)
    else:
        print("已导出 DOT 文件（本机未安装 Graphviz，可用 .dot 文件手动渲染）：",
              os.path.basename(dot_path))


def main():
    run_classification()
    run_regression()
    print()
    print("任务3 运行完毕：分类问题（wine）与回归问题（diabetes）的图片都在：", IMG_DIR)
    print("提示：想得到 graphviz 渲染的图，可先安装 Graphviz 程序并 pip install graphviz，再重新运行本脚本。")


if __name__ == "__main__":
    main()
