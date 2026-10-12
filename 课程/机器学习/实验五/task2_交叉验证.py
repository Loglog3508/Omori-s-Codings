# -*- coding: utf-8 -*-
"""
实验五 任务2：用 sklearn 实现交叉验证

对应指导书任务：
    1. 手写 KFold / StratifiedKFold 看划分过程；
    2. cross_val_score / cross_validate 做逻辑回归交叉验证；
    3. GridSearchCV 用交叉验证挑选决策树最大深度；
    4. 多模型交叉验证对比。
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import (KFold, StratifiedKFold, cross_val_score,
                                     cross_validate, train_test_split, GridSearchCV)
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
os.makedirs(IMG_DIR, exist_ok=True)


def demo_kfold_manual():
    print("=" * 70)
    print("1. 手写 KFold 与 StratifiedKFold 的划分过程")
    print("=" * 70)
    X = np.arange(12).reshape(6, 2)
    y = np.array([0, 0, 0, 1, 1, 1])
    kf = KFold(n_splits=3, shuffle=True, random_state=42)
    print("KFold（不保证类别比例）：")
    for fold, (train_idx, test_idx) in enumerate(kf.split(X), 1):
        print("  第 %d 折 | 训练索引 %s | 验证索引 %s" % (fold, [int(i) for i in train_idx], [int(i) for i in test_idx]))
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    print("StratifiedKFold（保持每折类别比例）：")
    for fold, (train_idx, test_idx) in enumerate(skf.split(X, y), 1):
        print("  第 %d 折 | 训练索引 %s | 验证索引 %s" % (fold, [int(i) for i in train_idx], [int(i) for i in test_idx]))


def demo_cross_val_score():
    print("=" * 70)
    print("2. cross_val_score / cross_validate：逻辑回归 5 折交叉验证")
    print("=" * 70)
    data = load_breast_cancer()
    X, y = data.data, data.target
    pipe = Pipeline([("scaler", StandardScaler()),
                     ("lr", LogisticRegression(max_iter=1000))])
    scores = cross_val_score(pipe, X, y,
                             cv=StratifiedKFold(5, shuffle=True, random_state=42),
                             scoring="accuracy")
    print("每折准确率：", np.round(scores, 4))
    print("平均准确率：%.4f ± %.4f" % (scores.mean(), scores.std()))
    res = cross_validate(pipe, X, y, cv=5,
                         scoring=["accuracy", "precision", "recall", "f1"])
    print("cross_validate 多指标（各折均值）：")
    for k in ["accuracy", "precision", "recall", "f1"]:
        print("  %-9s = %.4f" % (k, res["test_" + k].mean()))
    return scores


def demo_grid_search():
    print("=" * 70)
    print("3. GridSearchCV：用交叉验证挑选决策树最大深度")
    print("=" * 70)
    data = load_breast_cancer()
    X, y = data.data, data.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    param_grid = {"max_depth": [2, 3, 4, 5, 6, None]}
    gs = GridSearchCV(DecisionTreeClassifier(random_state=42), param_grid,
                      cv=5, scoring="accuracy")
    gs.fit(X_train, y_train)
    print("最优参数：", gs.best_params_)
    print("最优交叉验证准确率：%.4f" % gs.best_score_)
    print("测试集准确率：%.4f" % gs.score(X_test, y_test))
    means = gs.cv_results_["mean_test_score"]
    depths = ["2", "3", "4", "5", "6", "None"]
    plt.figure(figsize=(7, 4.5))
    bars = plt.bar(depths, means, color="#4C72B0")
    plt.xlabel("max_depth")
    plt.ylabel("交叉验证平均准确率")
    plt.title("决策树 max_depth 与交叉验证准确率（GridSearchCV）")
    plt.ylim(0.8, 1.0)
    for bar, v in zip(bars, means):
        plt.text(bar.get_x() + bar.get_width() / 2, v + 0.003, "%.4f" % v, ha="center", fontsize=9)
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task2_GridSearchCV_决策树深度选择.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("已保存：%s" % out)


def demo_model_compare():
    print("=" * 70)
    print("4. 多模型交叉验证对比")
    print("=" * 70)
    data = load_breast_cancer()
    X, y = data.data, data.target
    models = {
        "逻辑回归": Pipeline([("scaler", StandardScaler()),
                             ("m", LogisticRegression(max_iter=1000))]),
        "决策树": DecisionTreeClassifier(random_state=42),
        "SVM(RBF)": Pipeline([("scaler", StandardScaler()),
                             ("m", SVC())]),
    }
    names, means, stds = [], [], []
    for name, model in models.items():
        scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
        print("%-8s 平均准确率 = %.4f ± %.4f" % (name, scores.mean(), scores.std()))
        names.append(name)
        means.append(scores.mean())
        stds.append(scores.std())
    plt.figure(figsize=(7, 4.5))
    bars = plt.bar(names, means, yerr=stds, capsize=5,
                   color=["#4C72B0", "#55A868", "#C44E52"])
    plt.ylabel("5 折交叉验证平均准确率")
    plt.title("不同模型交叉验证准确率对比（乳腺癌数据集）")
    plt.ylim(0.8, 1.0)
    for bar, v in zip(bars, means):
        plt.text(bar.get_x() + bar.get_width() / 2, v + 0.005, "%.4f" % v, ha="center")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task2_多模型交叉验证对比.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("已保存：%s" % out)


if __name__ == "__main__":
    demo_kfold_manual()
    demo_cross_val_score()
    demo_grid_search()
    demo_model_compare()
