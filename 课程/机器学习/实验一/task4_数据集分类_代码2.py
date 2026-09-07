"""
实验一 任务4：用纯python代码2（牛顿法逻辑回归）对下面的数据集进行分类

数据集：鸢尾花数据集（load_iris）
    - 样本数：150
    - 特征数：4（花萼长、花萼宽、花瓣长、花瓣宽）
    - 类别数：3（山鸢尾、变色鸢尾、维吉尼亚鸢尾）
流程：
    1. 加载数据，划分训练集 / 测试集
    2. 特征标准化
    3. 使用纯python代码2中的 One-vs-Rest 牛顿法逻辑回归训练
    4. 评估并可视化（损失收敛速度比梯度下降更快，迭代次数更少）
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris

from 纯python代码2_牛顿法逻辑回归 import LogisticRegressionNewton, OneVsRestClassifier

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

IMG_DIR = os.path.join(os.path.dirname(__file__), "结果图")
os.makedirs(IMG_DIR, exist_ok=True)


def train_test_split_manual(X, y, test_size=0.3, random_state=42):
    rng = np.random.default_rng(random_state)
    m = X.shape[0]
    idx = rng.permutation(m)
    n_test = int(m * test_size)
    test_idx, train_idx = idx[:n_test], idx[n_test:]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def standardize(X_train, X_test):
    mean, std = X_train.mean(axis=0), X_train.std(axis=0)
    std[std == 0] = 1.0
    return (X_train - mean) / std, (X_test - mean) / std


def plot_decision_boundary(model, X2, y, title, filename):
    x_min, x_max = X2[:, 0].min() - 0.5, X2[:, 0].max() + 0.5
    y_min, y_max = X2[:, 1].min() - 0.5, X2[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 300),
                         np.linspace(y_min, y_max, 300))
    grid = np.c_[xx.ravel(), yy.ravel()]
    Z = np.argmax(model.predict_proba(grid), axis=1).reshape(xx.shape)

    plt.figure(figsize=(8, 6))
    plt.contourf(xx, yy, Z, alpha=0.35, cmap="Set2")
    plt.contour(xx, yy, Z, colors="k", linewidths=0.5, alpha=0.5)
    scatter = plt.scatter(X2[:, 0], X2[:, 1], c=y, cmap="Set2", edgecolor="k", s=40)
    plt.colorbar(scatter, label="类别")
    plt.xlabel("特征1（标准化后）")
    plt.ylabel("特征2（标准化后）")
    plt.title(title)
    out = os.path.join(IMG_DIR, filename)
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    print("决策边界图已保存：", out)


def main():
    # 1. 加载鸢尾花数据集
    iris = load_iris()
    X, y = iris.data, iris.target
    print("鸢尾花数据集形状：", X.shape, "，类别数：", len(np.unique(y)))

    # 2. 划分训练集 / 测试集
    X_train, X_test, y_train, y_test = train_test_split_manual(X, y, test_size=0.3)

    # 3. 特征标准化
    X_train_s, X_test_s = standardize(X_train, X_test)

    # 4. 用纯python代码2（牛顿法）训练 One-vs-Rest 逻辑回归
    model = OneVsRestClassifier(LogisticRegressionNewton, n_iterations=50, tolerance=1e-8)
    model.fit(X_train_s, y_train)

    # 5. 评估
    train_acc = model.score(X_train_s, y_train)
    test_acc = model.score(X_test_s, y_test)
    print(f"训练集准确率：{train_acc:.4f}")
    print(f"测试集准确率：{test_acc:.4f}")

    pred = model.predict(X_test_s)
    print("\n各类别测试结果：")
    for c in model.classes_:
        mask = y_test == c
        acc = np.mean(pred[mask] == c)
        print(f"  类别 {c}（{iris.target_names[c]}）：{acc:.4f}  （样本数 {mask.sum()}）")

    # 6. 可视化：牛顿法损失收敛（通常只需个位数迭代即可收敛）
    plt.figure(figsize=(8, 5))
    for c, clf in model.models.items():
        plt.plot(clf.loss_history, marker="o", markersize=4,
                 label=f"类别 {c} vs 其余")
    plt.xlabel("迭代次数")
    plt.ylabel("交叉熵损失")
    plt.title("纯python代码2：鸢尾花分类各二分类器损失收敛曲线（牛顿法）")
    plt.legend()
    plt.grid(alpha=0.3)
    out1 = os.path.join(IMG_DIR, "task4_鸢尾花分类_损失收敛曲线.png")
    plt.tight_layout()
    plt.savefig(out1, dpi=150)
    plt.close()
    print("损失曲线图已保存：", out1)
    print("牛顿法迭代轮数：", {int(c): len(clf.loss_history) for c, clf in model.models.items()})

    # 用前两个特征画决策边界
    X2_train, X2_test, _, _ = train_test_split_manual(X[:, :2], y, test_size=0.3)
    X2_train_s, X2_test_s = standardize(X2_train, X2_test)
    model2d = OneVsRestClassifier(LogisticRegressionNewton, n_iterations=50, tolerance=1e-8)
    model2d.fit(X2_train_s, y_train)
    plot_decision_boundary(model2d, np.vstack([X2_train_s, X2_test_s]),
                           np.hstack([y_train, y_test]),
                           "鸢尾花数据集（前2个特征）逻辑回归决策边界（牛顿法）",
                           "task4_鸢尾花分类_决策边界.png")
    print("2D 决策边界准确率：", round(model2d.score(X2_test_s, y_test), 4))


if __name__ == "__main__":
    main()
