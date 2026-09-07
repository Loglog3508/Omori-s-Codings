"""
实验一 任务3：用纯python代码1（梯度下降逻辑回归）对红酒数据集进行分类

数据集：sklearn 自带的红酒数据集（load_wine）
    - 样本数：178
    - 特征数：13（酒精含量、苹果酸、灰分等化学成分指标）
    - 类别数：3（三个产地的红酒）
流程：
    1. 加载数据，划分为训练集 / 测试集
    2. 特征标准化（z-score）
    3. 使用纯python代码1中的 One-vs-Rest 逻辑回归训练
    4. 评估分类效果并可视化
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_wine

from 纯python代码1_梯度下降逻辑回归 import LogisticRegressionGD, OneVsRestClassifier

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

IMG_DIR = os.path.join(os.path.dirname(__file__), "结果图")
os.makedirs(IMG_DIR, exist_ok=True)


def train_test_split_manual(X, y, test_size=0.3, random_state=42):
    """不使用 sklearn，手动划分训练集与测试集"""
    rng = np.random.default_rng(random_state)
    m = X.shape[0]
    idx = rng.permutation(m)
    n_test = int(m * test_size)
    test_idx, train_idx = idx[:n_test], idx[n_test:]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def standardize(X_train, X_test):
    """z-score 标准化：用训练集的均值/标准差处理训练集和测试集"""
    mean, std = X_train.mean(axis=0), X_train.std(axis=0)
    std[std == 0] = 1.0
    return (X_train - mean) / std, (X_test - mean) / std


def plot_decision_boundary(model, X2, y, title, filename):
    """仅用前两个特征绘制二维决策边界（用于直观展示分类效果）"""
    x_min, x_max = X2[:, 0].min() - 0.5, X2[:, 0].max() + 0.5
    y_min, y_max = X2[:, 1].min() - 0.5, X2[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 300),
                         np.linspace(y_min, y_max, 300))
    grid = np.c_[xx.ravel(), yy.ravel()]
    Z = model.predict_proba(grid)
    Z = np.argmax(Z, axis=1).reshape(xx.shape)

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
    # 1. 加载红酒数据集
    wine = load_wine()
    X, y = wine.data, wine.target
    print("红酒数据集形状：", X.shape, "，类别数：", len(np.unique(y)))

    # 2. 划分训练集 / 测试集
    X_train, X_test, y_train, y_test = train_test_split_manual(X, y, test_size=0.3)

    # 3. 特征标准化
    X_train_s, X_test_s = standardize(X_train, X_test)

    # 4. 用纯python代码1（梯度下降）训练 One-vs-Rest 逻辑回归
    model = OneVsRestClassifier(LogisticRegressionGD,
                                learning_rate=0.2, n_iterations=3000, tolerance=1e-7)
    model.fit(X_train_s, y_train)

    # 5. 评估
    train_acc = model.score(X_train_s, y_train)
    test_acc = model.score(X_test_s, y_test)
    print(f"训练集准确率：{train_acc:.4f}")
    print(f"测试集准确率：{test_acc:.4f}")

    # 逐类别准确率
    pred = model.predict(X_test_s)
    print("\n各类别测试结果：")
    for c in model.classes_:
        mask = y_test == c
        acc = np.mean(pred[mask] == c)
        print(f"  类别 {c}（{wine.target_names[c]}）：{acc:.4f}  （样本数 {mask.sum()}）")

    # 6. 可视化
    # (a) 三个二分类器的损失收敛曲线
    plt.figure(figsize=(8, 5))
    for c, clf in model.models.items():
        plt.plot(clf.loss_history, label=f"类别 {c} vs 其余")
    plt.xlabel("迭代次数")
    plt.ylabel("交叉熵损失")
    plt.title("纯python代码1：红酒分类各二分类器损失收敛曲线")
    plt.legend()
    plt.grid(alpha=0.3)
    out1 = os.path.join(IMG_DIR, "task3_红酒分类_损失收敛曲线.png")
    plt.tight_layout()
    plt.savefig(out1, dpi=150)
    plt.close()
    print("损失曲线图已保存：", out1)

    # (b) 用前两个特征画决策边界（可视化用）
    X2_train, X2_test, _, _ = train_test_split_manual(X[:, :2], y, test_size=0.3)
    X2_train_s, X2_test_s = standardize(X2_train, X2_test)
    model2d = OneVsRestClassifier(LogisticRegressionGD,
                                  learning_rate=0.3, n_iterations=3000, tolerance=1e-7)
    model2d.fit(X2_train_s, y_train)
    plot_decision_boundary(model2d, np.vstack([X2_train_s, X2_test_s]),
                           np.hstack([y_train, y_test]),
                           "红酒数据集（前2个特征）逻辑回归决策边界",
                           "task3_红酒分类_决策边界.png")
    print("2D 决策边界准确率：", round(model2d.score(X2_test_s, y_test), 4))


if __name__ == "__main__":
    main()
