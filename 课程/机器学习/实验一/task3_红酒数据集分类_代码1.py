"""
实验一 任务3：用纯python代码1对红酒数据集进行分类

纯python代码1（老师提供）：纯python代码1/logistic_regression.py
    用批量梯度下降从零实现的二分类逻辑回归
    （class LogisticRegression，接口为 train(X, y) / predict(X)，
      内部自动为 X 增加一列 x0 = 1 作为偏置项）。

数据集（老师提供）：纯python代码1/wine.data —— UCI Wine 红酒数据集的二分类子集
    - 样本数：130
    - 特征数：13（酒精、苹果酸、灰分、镁、脯氨酸等化学成分指标）
    - 类别数：2（class 1 / class 2）

流程：
    1. 读取 wine.data（第 1 列是类别，后 13 列是特征）；
    2. 划分训练集 / 测试集；
    3. 特征标准化——13 个特征量纲差别极大（如脯氨酸 278~1680，苹果酸只有 0.74~5.8），
       不标准化时梯度下降会震荡甚至数值溢出，标准化后收敛又快又稳；
    4. 用老师提供的 LogisticRegression（梯度下降）训练；
    5. 评估（准确率、混淆矩阵）并可视化（损失收敛曲线、二维决策边界）。
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
os.makedirs(IMG_DIR, exist_ok=True)

# 把老师提供的“纯python代码1”目录加入搜索路径，直接复用其中的 LogisticRegression
sys.path.insert(0, os.path.join(BASE, "纯python代码1"))
from logistic_regression import LogisticRegression


def load_wine_data(path):
    """读取老师提供的 wine.data：第 1 列是类别(1/2)，其余 13 列是特征"""
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append([float(v) for v in line.split(",")])
    data = np.array(rows)
    y = (data[:, 0].astype(int) == 2).astype(int)      # 类别 1→0，2→1
    X = data[:, 1:]
    return X, y


def train_test_split_manual(X, y, test_size=0.3, random_state=42):
    """不使用 sklearn，手动划分训练集与测试集"""
    rng = np.random.default_rng(random_state)
    idx = rng.permutation(len(y))
    n_test = int(len(y) * test_size)
    test_idx, train_idx = idx[:n_test], idx[n_test:]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def standardize(X_train, X_test):
    """z-score 标准化：用训练集的均值/标准差处理训练集和测试集"""
    mean, std = X_train.mean(axis=0), X_train.std(axis=0)
    std[std == 0] = 1.0
    return (X_train - mean) / std, (X_test - mean) / std

# wine.names 中给出的 13 个特征名称
FEATURE_NAMES = ["Alcohol", "Malic acid", "Ash", "Alcalinity of ash", "Magnesium",
                 "Total phenols", "Flavanoids", "Nonflavanoid phenols", "Proanthocyanins",
                 "Color intensity", "Hue", "OD280/OD315", "Proline"]


def main():
    # ---------------------------------------------------------- 1. 读取数据
    data_path = os.path.join(BASE, "纯python代码1", "wine.data")
    X_raw, y = load_wine_data(data_path)
    print("红酒数据集（老师提供）：", X_raw.shape, "，类别数：", len(np.unique(y)))
    print("每类样本数（class 1 / class 2）：", np.bincount(y).tolist())

    # ------------------------------------------------ 2. 划分 + 标准化
    X_train_raw, X_test_raw, y_train, y_test = train_test_split_manual(X_raw, y, test_size=0.3)
    X_train, X_test = standardize(X_train_raw, X_test_raw)

    # ----------------------------- 3. 直接用老师提供的纯python代码1训练
    np.random.seed(42)          # 老师的代码用随机数初始化 w，这里固定随机种子以便复现
    model = LogisticRegression(n_iter=5000, eta=0.5)
    model.train(X_train, y_train)

    # ---------------------------------------------------------- 4. 评估
    pred_train = model.predict(X_train)
    pred_test = model.predict(X_test)
    print("\n=== 梯度下降逻辑回归（老师提供的纯python代码1）===")
    print("训练集准确率：%.4f" % np.mean(pred_train == y_train))
    print("测试集准确率：%.4f" % np.mean(pred_test == y_test))
    print("最终损失：%.4f" % model.loss_list[-1])

    cm = confusion_matrix(y_test, pred_test)
    print("混淆矩阵（行=真实类别，列=预测类别）：\n", cm)

    # -------------------------------------------------- 5. 损失收敛曲线
    plt.figure(figsize=(8, 5))
    plt.plot(model.loss_list, color="#2c7fb8", lw=2)
    plt.xlabel("迭代次数")
    plt.ylabel("交叉熵损失")
    plt.title("任务3：红酒分类损失收敛曲线（纯python代码1，梯度下降）")
    plt.grid(alpha=0.3)
    out = os.path.join(IMG_DIR, "task3_红酒分类_损失收敛曲线.png")
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    print("损失收敛曲线已保存：", out)

    # ------------------------------------------------------ 6. 混淆矩阵
    disp = ConfusionMatrixDisplay(cm, display_labels=["class 1", "class 2"])
    disp.plot(cmap="Blues")
    plt.title("任务3：红酒分类混淆矩阵（纯python代码1）")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task3_红酒分类_混淆矩阵.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("混淆矩阵图已保存：", out)

    # ------------------------- 7. 用前两个特征画二维决策边界
    X2_train_raw, X2_test_raw, _, _ = train_test_split_manual(X_raw[:, :2], y, test_size=0.3)
    X2_train, X2_test = standardize(X2_train_raw, X2_test_raw)
    np.random.seed(42)
    model2d = LogisticRegression(n_iter=3000, eta=0.5)
    model2d.train(X2_train, y_train)

    x_min, x_max = X2_train[:, 0].min() - 0.5, X2_train[:, 0].max() + 0.5
    y_min, y_max = X2_train[:, 1].min() - 0.5, X2_train[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 300), np.linspace(y_min, y_max, 300))
    Z = model2d.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

    plt.figure(figsize=(8, 6))
    plt.contourf(xx, yy, Z, alpha=0.3, cmap="Set2")
    plt.contour(xx, yy, Z, colors="k", linewidths=0.8)
    plt.scatter(X2_train[:, 0], X2_train[:, 1], c=y_train, cmap="Set2",
                edgecolor="k", s=50, label="训练集")
    plt.scatter(X2_test[:, 0], X2_test[:, 1], c=y_test, cmap="Set2",
                edgecolor="k", s=50, marker="^", label="测试集")
    plt.xlabel("特征1（酒精，标准化后）")
    plt.ylabel("特征2（苹果酸，标准化后）")
    plt.title("任务3：红酒分类决策边界（前 2 个特征，梯度下降逻辑回归）")
    plt.legend()
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task3_红酒分类_决策边界.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("决策边界图已保存：", out)
    print("仅用前 2 个特征时的测试集准确率：",
          round(float(np.mean(model2d.predict(X2_test) == y_test)), 4))

    # -------------------------------------- 8. 看一下各特征的权重（已标准化）
    w = model.w[1:]                      # 第 0 个是偏置
    order = np.argsort(np.abs(w))[::-1]
    print("\n对分类影响最大的特征（标准化后权重绝对值前 5）：")
    for i in order[:5]:
        print(f"  {FEATURE_NAMES[i]}：权重 {w[i]:.3f}")


if __name__ == "__main__":
    main()