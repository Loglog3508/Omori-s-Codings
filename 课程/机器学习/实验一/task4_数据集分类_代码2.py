"""
实验一 任务4：用纯python代码2对下面的数据集进行分类

纯python代码2（老师提供）：纯python代码2/lr_train.py、纯python代码2/lr_test.py
    - lr_train.py：load_data() 读入制表符分隔的数据，lr_train_bgd() 用批量梯度下降训练逻辑回归，
                   error_rate() 计算损失，save_model() 保存权重；
    - lr_test.py ：load_weight() 载入权重，load_data() 读取测试集，predict() 输出 0/1 预测，
                   save_result() 保存预测结果。

数据集（老师提供）：
    - 纯python代码2/data.txt ：200 个样本、2 个特征，最后 1 列是类别标签（0/1）
    - 纯python代码2/test_data：200 个样本、2 个特征，没有标签

说明：lr_train.py / lr_test.py 中使用了 np.mat，而 NumPy 2.0 已经移除该函数，
      因此脚本开头加了兼容处理 np.mat = np.asmatrix，让老师提供的代码可以直接运行。

流程：
    1. 完整复现老师代码 2 的原始流程：用 data.txt 训练 → 保存权重 weights
       → 用 test_data 预测 → 保存结果 result；
    2. 为了能计算准确率等指标，再把 data.txt 按 7:3 划分成训练集/测试集
       （写成与原文件相同格式的临时文件），用 lr_train_bgd() 训练、用 lr_test.predict() 预测，
       评估准确率并画混淆矩阵；
    3. 可视化：损失收敛曲线、二维决策边界。
"""
import os
import sys
import io
import contextlib
import tempfile
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

if not hasattr(np, "mat"):          # NumPy 2.0 移除了 np.mat，这里做兼容
    np.mat = np.asmatrix

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
CODE2_DIR = os.path.join(BASE, "纯python代码2")
os.makedirs(IMG_DIR, exist_ok=True)

# 把老师提供的“纯python代码2”目录加入搜索路径，直接复用其中的函数
sys.path.insert(0, CODE2_DIR)
import lr_train
import lr_test


def read_matrix(path, has_label=True):
    """把制表符分隔的文本读成 (X, y) 两个 ndarray"""
    X, y = [], []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            vals = [float(v) for v in line.split("\t")]
            if has_label:
                X.append(vals[:-1])
                y.append(vals[-1])
            else:
                X.append(vals)
    X = np.array(X)
    y = np.array(y).astype(int) if has_label else None
    return X, y


def write_matrix(path, X, y=None):
    """按老师代码2的格式（制表符分隔）写文件"""
    with open(path, "w", encoding="utf-8") as f:
        for i in range(len(X)):
            if y is None:
                f.write("\t".join(str(v) for v in X[i]) + "\n")
            else:
                f.write("\t".join(str(v) for v in X[i]) + "\t" + str(y[i]) + "\n")

def run_original_flow():
    """完整复现老师代码 2 的原始流程：data.txt 训练 → weights → test_data 预测 → result"""
    cwd = os.getcwd()
    os.chdir(CODE2_DIR)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            feature, label = lr_train.load_data("data.txt")
            w = lr_train.lr_train_bgd(feature, label, 1000, 0.01)   # 老师代码里的默认参数
            lr_train.save_model("weights", w)
            w_loaded = lr_test.load_weight("weights")
            test_mat = lr_test.load_data("test_data", np.shape(w_loaded)[1])
            h = lr_test.predict(test_mat, w_loaded)
            lr_test.save_result("result", h)
    finally:
        os.chdir(cwd)
    return w, np.asarray(h).ravel().astype(int)


def main():
    data_path = os.path.join(CODE2_DIR, "data.txt")

    # ---------------------- 1. 复现老师代码2的原始流程 ----------------------
    print("=== 1. 完整复现老师代码2的原始流程（data.txt 训练 → test_data 预测）===")
    w, pred_test_data = run_original_flow()
    print("训练得到的权重 w（含偏置项）：", np.round(np.asarray(w).ravel(), 4).tolist())
    print("已在 纯python代码2/ 目录生成 weights（权重）与 result（对 test_data 的预测结果）")
    print("test_data 中被预测为类别 1 的样本数：", int(pred_test_data.sum()), "/", len(pred_test_data))

    # ---------------------- 2. 划分训练/测试集并评估 ----------------------
    X, y = read_matrix(data_path, has_label=True)
    print("\n=== 2. 把 data.txt 按 7:3 划分训练/测试集，评估分类效果 ===")
    print("数据形状：", X.shape, "，两类样本数：", np.bincount(y).tolist())

    rng = np.random.default_rng(42)
    idx = rng.permutation(len(y))
    n_test = int(len(y) * 0.3)
    test_idx, train_idx = idx[:n_test], idx[n_test:]

    with tempfile.TemporaryDirectory() as tmp:
        train_file = os.path.join(tmp, "train_data")
        test_file = os.path.join(tmp, "test_feature")
        write_matrix(train_file, X[train_idx], y[train_idx])
        write_matrix(test_file, X[test_idx])          # 测试集只写特征，格式与 test_data 相同

        with contextlib.redirect_stdout(io.StringIO()):
            feature, label = lr_train.load_data(train_file)
            w_split = lr_train.lr_train_bgd(feature, label, 2000, 0.1)
            lr_train.save_model(os.path.join(tmp, "weights"), w_split)
            w_row = lr_test.load_weight(os.path.join(tmp, "weights"))
            test_mat = lr_test.load_data(test_file, np.shape(w_row)[1])
            pred = np.asarray(lr_test.predict(test_mat, w_row)).ravel().astype(int)

        loss = lr_train.error_rate(lr_train.sig(feature * w_split), label)
        acc = float(np.mean(pred == y[test_idx]))
        print("训练集损失 error_rate = %.6f" % loss)
        print("测试集准确率 = %.4f（测试集 %d 个样本）" % (acc, n_test))
        cm = confusion_matrix(y[test_idx], pred)
        print("混淆矩阵（行=真实类别，列=预测类别）：\n", cm)

    # ---------------------- 3. 混淆矩阵 ----------------------
    disp = ConfusionMatrixDisplay(cm, display_labels=["类别 0", "类别 1"])
    disp.plot(cmap="Blues")
    plt.title("任务4：数据集分类混淆矩阵（纯python代码2）")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task4_数据集分类_混淆矩阵.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("混淆矩阵图已保存：", out)

    # ---------------------- 4. 损失收敛曲线 ----------------------
    cycles = [10, 25, 50, 100, 200, 400, 700, 1000, 1500, 2000]
    losses = []
    with contextlib.redirect_stdout(io.StringIO()):
        feature_all, label_all = lr_train.load_data(data_path)
        for c in cycles:
            w_c = lr_train.lr_train_bgd(feature_all, label_all, c, 0.1)
            losses.append(float(lr_train.error_rate(lr_train.sig(feature_all * w_c), label_all)))

    plt.figure(figsize=(8, 5))
    plt.semilogy(cycles, losses, "o-", color="#2c7fb8")
    plt.xlabel("迭代次数")
    plt.ylabel("交叉熵损失（对数刻度）")
    plt.title("任务4：损失随迭代次数的下降（纯python代码2，批量梯度下降）")
    plt.grid(alpha=0.3, which="both")
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task4_数据集分类_损失收敛曲线.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("损失收敛曲线已保存：", out)

    # ---------------------- 5. 二维决策边界 ----------------------
    with tempfile.TemporaryDirectory() as tmp:
        w_path = os.path.join(tmp, "weights")
        with contextlib.redirect_stdout(io.StringIO()):
            w_all = lr_train.lr_train_bgd(feature_all, label_all, 2000, 0.1)
            lr_train.save_model(w_path, w_all)
            w_row = lr_test.load_weight(w_path)

        x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
        y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
        xx, yy = np.meshgrid(np.linspace(x_min, x_max, 300), np.linspace(y_min, y_max, 300))
        grid = np.c_[xx.ravel(), yy.ravel()]
        grid_mat = np.mat(np.c_[np.ones(len(grid)), grid])     # 加上偏置列 x0 = 1
        Z = np.asarray(lr_test.predict(grid_mat, w_row)).ravel().reshape(xx.shape)

    plt.figure(figsize=(8, 6))
    plt.contourf(xx, yy, Z, alpha=0.3, cmap="Set1")
    plt.contour(xx, yy, Z, colors="k", linewidths=0.8)
    plt.scatter(X[y == 0, 0], X[y == 0, 1], c="#4d4d4d", edgecolor="k", s=45, label="类别 0")
    plt.scatter(X[y == 1, 0], X[y == 1, 1], c="#e6550d", edgecolor="k", s=45, label="类别 1")
    plt.xlabel("特征 1")
    plt.ylabel("特征 2")
    plt.title("任务4：二维数据上的逻辑回归决策边界（纯python代码2）")
    plt.legend()
    plt.tight_layout()
    out = os.path.join(IMG_DIR, "task4_数据集分类_决策边界.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print("决策边界图已保存：", out)

    h_all = lr_train.sig(feature_all * w_all)
    acc_all = float(np.mean((np.asarray(h_all) >= 0.5).astype(int) == np.asarray(label_all)))
    print("在全部 200 个样本上的训练准确率：%.4f" % acc_all)


if __name__ == "__main__":
    main()