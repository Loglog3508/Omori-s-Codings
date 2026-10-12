# -*- coding: utf-8 -*-
"""
实验六 综合练习：用多种机器学习算法解决乳腺癌良恶性诊断问题

题目：从目前所学算法中选取一种或多种算法解决实际中的问题，并写清处理流程和核心算法。

本练习选取「乳腺癌良恶性诊断」这个实际二分类问题，串联本学期学过的算法：
    - 实验二：K-Means 聚类做无监督探索；
    - 实验五：数据预处理(StandardScaler) + 交叉验证(StratifiedKFold / cross_val_score)；
    - 实验一：逻辑回归；
    - 实验三：决策树（含可视化）；
    - 实验四：神经网络(MLPClassifier)；
    - 对照模型：SVM。

处理流程：
    1) 数据探索（样本、特征、类别分布）
    2) 无监督探索（K-Means 聚类 + PCA 可视化）
    3) 多模型 5 折交叉验证对比
    4) 选最优模型做最终评估（准确率/精确率/召回率/F1/混淆矩阵/ROC）
    5) 决策树可视化
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             confusion_matrix, ConfusionMatrixDisplay, classification_report,
                             roc_curve, auc, adjusted_rand_score)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
os.makedirs(IMG_DIR, exist_ok=True)
RANDOM = 42


def load_and_explore():
    print("=" * 78)
    print("一、问题定义与数据探索")
    print("=" * 78)
    data = load_breast_cancer()
    X, y = data.data, data.target
    print("问题：根据 30 个细胞核特征判断乳腺肿瘤是恶性(0)还是良性(1)。")
    print("样本数：%d，特征数：%d" % X.shape)
    print("特征名：")
    print("  " + ", ".join(data.feature_names))
    print("类别分布：恶性 %d，良性 %d" % (int((y == 0).sum()), int((y == 1).sum())))
    return X, y, data


def clustering_explore(X, y):
    print("=" * 78)
    print("二、无监督探索：K-Means 聚类（实验二方法）")
    print("=" * 78)
    X_s = StandardScaler().fit_transform(X)
    km = KMeans(n_clusters=2, random_state=RANDOM, n_init=10)
    labels = km.fit_predict(X_s)
    ari = adjusted_rand_score(y, labels)
    print("K-Means(2 类) 与真实标签的调整兰德指数 ARI：%.4f" % ari)
    print("聚类标签分布：", np.bincount(labels))
    pca = PCA(n_components=2, random_state=RANDOM)
    X_pca = pca.fit_transform(X_s)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].scatter(X_pca[y == 0, 0], X_pca[y == 0, 1], c="#C44E52", label="恶性", alpha=0.7)
    axes[0].scatter(X_pca[y == 1, 0], X_pca[y == 1, 1], c="#4C72B0", label="良性", alpha=0.7)
    axes[0].set_title("真实标签")
    axes[0].legend()
    axes[1].scatter(X_pca[labels == 0, 0], X_pca[labels == 0, 1], c="#C44E52", label="簇 0", alpha=0.7)
    axes[1].scatter(X_pca[labels == 1, 0], X_pca[labels == 1, 1], c="#4C72B0", label="簇 1", alpha=0.7)
    axes[1].set_title("K-Means 聚类结果 (ARI=%.3f)" % ari)
    axes[1].legend()
    for ax in axes:
        ax.set_xlabel("PCA 成分 1")
        ax.set_ylabel("PCA 成分 2")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task_聚类探索_PCA.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("已保存：%s" % out)


def model_compare(X, y):
    print("=" * 78)
    print("三、有监督模型对比（5 折交叉验证，实验五方法）")
    print("=" * 78)
    models = {
        "逻辑回归\n(实验一)": Pipeline([("scaler", StandardScaler()),
                                        ("m", LogisticRegression(max_iter=2000))]),
        "决策树\n(实验三)": DecisionTreeClassifier(max_depth=4, random_state=RANDOM),
        "SVM(RBF)": Pipeline([("scaler", StandardScaler()),
                              ("m", SVC(random_state=RANDOM))]),
        "神经网络MLP\n(实验四)": Pipeline([("scaler", StandardScaler()),
                                          ("m", MLPClassifier(hidden_layer_sizes=(32, 16),
                                                              max_iter=1000, random_state=RANDOM))]),
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM)
    names, means, stds = [], [], []
    print("%-20s %s" % ("模型", "5 折交叉验证准确率"))
    for name, model in models.items():
        scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
        names.append(name)
        means.append(scores.mean())
        stds.append(scores.std())
        print("%-20s %.4f ± %.4f" % (name.replace("\n", " "), scores.mean(), scores.std()))
    plt.figure(figsize=(9, 5))
    bars = plt.bar(names, means, yerr=stds, capsize=5,
                   color=["#4C72B0", "#55A868", "#C44E52", "#8172B2"])
    plt.ylabel("5 折交叉验证平均准确率")
    plt.title("四种算法在乳腺癌诊断上的交叉验证对比")
    plt.ylim(0.8, 1.0)
    for bar, v in zip(bars, means):
        plt.text(bar.get_x() + bar.get_width() / 2, v + 0.004, "%.4f" % v, ha="center")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task_多模型交叉验证对比.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("已保存：%s" % out)
    return models


def evaluate_best(X, y):
    print("=" * 78)
    print("四、选最优模型（逻辑回归）做最终评估")
    print("=" * 78)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM, stratify=y)
    pipe = Pipeline([("scaler", StandardScaler()),
                     ("m", LogisticRegression(max_iter=2000))])
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)[:, 1]
    print("测试集准确率：%.4f" % accuracy_score(y_test, y_pred))
    print("精确率：%.4f  召回率：%.4f  F1：%.4f" % (
        precision_score(y_test, y_pred), recall_score(y_test, y_pred), f1_score(y_test, y_pred)))
    print("\n分类报告：")
    print(classification_report(y_test, y_pred, target_names=["恶性", "良性"]))
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(cm, display_labels=["恶性", "良性"])
    disp.plot(cmap="Blues", values_format="d")
    plt.title("逻辑回归混淆矩阵")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task_混淆矩阵.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("已保存：%s" % out)
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, color="#4C72B0", lw=2, label="ROC 曲线 (AUC=%.4f)" % roc_auc)
    plt.plot([0, 1], [0, 1], "k--", lw=1)
    plt.xlabel("假正率 FPR")
    plt.ylabel("真正率 TPR")
    plt.title("逻辑回归 ROC 曲线")
    plt.legend(loc="lower right")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task_ROC曲线.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("已保存：%s" % out)


def tree_viz(X, y, data):
    print("=" * 78)
    print("五、决策树可视化（实验三方法）")
    print("=" * 78)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM, stratify=y)
    tree = DecisionTreeClassifier(max_depth=3, random_state=RANDOM)
    tree.fit(X_train, y_train)
    print("决策树(max_depth=3) 测试准确率：%.4f" % tree.score(X_test, y_test))
    plt.figure(figsize=(16, 9))
    plot_tree(tree, feature_names=data.feature_names, class_names=["恶性", "良性"],
              filled=True, rounded=True, fontsize=8)
    plt.title("乳腺癌诊断决策树（max_depth=3）")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task_决策树可视化.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print("已保存：%s" % out)


if __name__ == "__main__":
    X, y, data = load_and_explore()
    clustering_explore(X, y)
    model_compare(X, y)
    evaluate_best(X, y)
    tree_viz(X, y, data)
    print("\n实验六完成，所有结果图已保存到 %s" % IMG_DIR)
