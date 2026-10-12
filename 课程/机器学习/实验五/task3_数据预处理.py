# -*- coding: utf-8 -*-
"""
实验五 任务3：用 sklearn 实现数据预处理

对应指导书任务：
    1. 对比 StandardScaler / MinMaxScaler / RobustScaler 对特征分布的影响；
    2. 类别编码 LabelEncoder 与 OneHotEncoder；
    3. 展示缩放对 KNN 这类距离模型性能的影响。
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import (StandardScaler, MinMaxScaler, RobustScaler,
                                   LabelEncoder, OneHotEncoder)
from sklearn.neighbors import KNeighborsClassifier

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
os.makedirs(IMG_DIR, exist_ok=True)


def demo_scalers():
    print("=" * 70)
    print("1. 三种缩放器对特征分布的影响")
    print("=" * 70)
    data = load_breast_cancer()
    X = data.data
    col = 2  # mean perimeter，量纲与其它特征差异明显
    raw = X[:, col]
    scalers = {
        "原始数据": None,
        "StandardScaler 标准化": StandardScaler(),
        "MinMaxScaler 归一化": MinMaxScaler(),
        "RobustScaler 稳健缩放": RobustScaler(),
    }
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.6))
    for ax, (name, scaler) in zip(axes, scalers.items()):
        if scaler is None:
            v = raw
        else:
            v = scaler.fit_transform(raw.reshape(-1, 1)).ravel()
        ax.hist(v, bins=30, color="#4C72B0", alpha=0.8)
        ax.set_title(name)
        ax.set_xlabel(data.feature_names[col] + " 的取值")
    plt.suptitle("不同缩放方式对特征分布的影响", fontsize=13)
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task3_数据缩放对比.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("已保存：%s" % out)


def demo_label_encoding():
    print("=" * 70)
    print("2. 类别编码：LabelEncoder 与 OneHotEncoder")
    print("=" * 70)
    labels = ["苹果", "香蕉", "苹果", "橙子", "香蕉"]
    le = LabelEncoder()
    encoded = le.fit_transform(labels)
    print("原始标签：", labels)
    print("LabelEncoder 结果：", encoded)
    print("类别映射：", {str(k): int(v) for k, v in zip(le.classes_, le.transform(le.classes_))})
    ohe = OneHotEncoder(sparse_output=False)
    onehot = ohe.fit_transform(np.array(labels).reshape(-1, 1))
    print("OneHotEncoder 特征名：", ohe.get_feature_names_out())
    print("OneHot 结果：")
    print(onehot)


def demo_scaling_effect():
    print("=" * 70)
    print("3. 缩放对 KNN 的影响（缩放前 vs 缩放后）")
    print("=" * 70)
    data = load_breast_cancer()
    X, y = data.data, data.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(X_train, y_train)
    acc_raw = knn.score(X_test, y_test)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    knn.fit(X_train_s, y_train)
    acc_scaled = knn.score(X_test_s, y_test)
    print("不缩放     KNN 测试准确率：%.4f" % acc_raw)
    print("标准化后   KNN 测试准确率：%.4f" % acc_scaled)
    print("结论：距离类模型对特征量纲敏感，标准化后可明显提升性能。")


if __name__ == "__main__":
    demo_scalers()
    demo_label_encoding()
    demo_scaling_effect()
