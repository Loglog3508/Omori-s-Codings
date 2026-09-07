"""
实验一 任务5：自选数据集，使用逻辑回归解决一个分类问题

自选数据集：威斯康星乳腺癌数据集（load_breast_cancer）
    - 样本数：569
    - 特征数：30（细胞核的半径、纹理、周长、面积等形态学指标）
    - 类别：0 = 恶性（malignant），1 = 良性（benign）
    - 问题：根据细胞特征预测肿瘤是良性还是恶性（二分类）

实现方式：使用 sklearn 机器学习框架中的 LogisticRegression，
并配合 train_test_split、StandardScaler 与评估指标（准确率、精确率、
召回率、F1、混淆矩阵、ROC 曲线）。
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix, ConfusionMatrixDisplay,
                             roc_curve, auc)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

IMG_DIR = os.path.join(os.path.dirname(__file__), "结果图")
os.makedirs(IMG_DIR, exist_ok=True)


def main():
    # 1. 加载数据
    cancer = load_breast_cancer()
    X, y = cancer.data, cancer.target
    print("数据集形状：", X.shape)
    print("类别分布：", dict(zip(*np.unique(y, return_counts=True))))
    print("类别含义：", dict(enumerate(cancer.target_names)))

    # 2. 划分训练集 / 测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y)

    # 3. 数据预处理：标准化（逻辑回归对特征尺度敏感）
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # 4. 训练逻辑回归模型（sklearn）
    model = LogisticRegression(max_iter=2000, C=1.0, random_state=42)
    model.fit(X_train_s, y_train)

    # 5. 预测与评估
    y_pred = model.predict(X_test_s)
    y_prob = model.predict_proba(X_test_s)[:, 1]

    print("\n=== 测试集评估结果 ===")
    print("准确率 Accuracy :", round(accuracy_score(y_test, y_pred), 4))
    print("精确率 Precision:", round(precision_score(y_test, y_pred), 4))
    print("召回率 Recall   :", round(recall_score(y_test, y_pred), 4))
    print("F1 值 F1-score  :", round(f1_score(y_test, y_pred), 4))

    # 混淆矩阵
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(cm, display_labels=cancer.target_names)
    disp.plot(cmap="Blues")
    plt.title("乳腺癌分类混淆矩阵")
    out1 = os.path.join(IMG_DIR, "task5_乳腺癌分类_混淆矩阵.png")
    plt.tight_layout()
    plt.savefig(out1, dpi=150)
    plt.close()
    print("\n混淆矩阵图已保存：", out1)
    print("混淆矩阵：\n", cm)

    # ROC 曲线
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, color="#d62728", lw=2, label=f"逻辑回归 (AUC = {roc_auc:.4f})")
    plt.plot([0, 1], [0, 1], "k--", lw=1, label="随机猜测")
    plt.xlabel("假正率 (FPR)")
    plt.ylabel("真正率 (TPR)")
    plt.title("乳腺癌分类 ROC 曲线")
    plt.legend()
    plt.grid(alpha=0.3)
    out2 = os.path.join(IMG_DIR, "task5_乳腺癌分类_ROC曲线.png")
    plt.tight_layout()
    plt.savefig(out2, dpi=150)
    plt.close()
    print("ROC 曲线图已保存：", out2)
    print("AUC =", round(roc_auc, 4))

    # 6. 展示最重要的特征（系数绝对值）
    coef = np.abs(model.coef_[0])
    top_idx = np.argsort(coef)[::-1][:8]
    print("\n对分类影响最大的特征：")
    for i in top_idx:
        print(f"  {cancer.feature_names[i]}：系数 {model.coef_[0][i]:.3f}")


if __name__ == "__main__":
    main()
