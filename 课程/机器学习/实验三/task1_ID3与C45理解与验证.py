# -*- coding: utf-8 -*-
"""
实验三 任务1：理解纯python代码2中实现 ID3 和 C4.5 算法

课程提供的代码（未做改动）：纯python代码2/id3.py、纯python代码2/c45.py
    - id3.py：只能处理离散特征，用“信息增益”选择分裂特征；
    - c45.py：既能处理离散特征，又能处理连续特征；离散特征用“信息增益率”选择，
              连续特征则枚举相邻取值的中点作为分裂点，取信息增益率最大的那个。

本脚本做四件事：
    1. 手算验证：在天气数据集上手动计算标签的信息熵、各特征的信息增益（ID3 的准则）
       和信息增益率（C4.5 的准则），用数据说明两者“选特征”的差异；
    2. 调用 ID3 代码在 weather_nominal.csv（全离散）上建树、分类、可视化和导出 DOT；
    3. 调用 C4.5 代码在 weather_numeric.csv（含连续特征）上建树、分类、可视化和导出 DOT；
    4. 用 sklearn 的决策树在同样数据上做对比，并画出“熵之半 / Gini 系数”曲线。

运行：python task1_ID3与C45理解与验证.py
说明：现有代码的 c45.py 在多数投票函数里带了调试用的 print，脚本用上下文管理器把这段
      打印临时静音，保证控制台输出整洁；源代码本身不做任何改动。
"""
import os
import sys
import io
import contextlib
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "结果图")
os.makedirs(IMG_DIR, exist_ok=True)

# 把课程提供的纯python代码2加入搜索路径，直接复用其中的函数
# （代码放在“决策树/纯python代码1”“决策树/纯python代码2”两个子文件夹里）
CODE_DIR = os.path.join(BASE, "决策树")
sys.path.insert(0, os.path.join(CODE_DIR, "纯python代码2"))
import id3          # noqa: E402  课程提供的 ID3 代码
import c45          # noqa: E402  课程提供的 C4.5 代码

import dt_utils     # noqa: E402  本实验的公共绘图工具


# 兼容补丁：现有代码/示例基于旧版 NumPy，np.mat 别名在 NumPy 2.0 中已被移除
if not hasattr(np, "mat"):
    np.mat = np.asmatrix


@contextlib.contextmanager
def quiet():
    """临时屏蔽现有代码里的调试打印（不改动源代码）"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield buf


def load_dataset(file_name, delimiter=","):
    """读取 CSV 数据集，返回 np.mat（与demo 的加载方式保持一致，元素为字符串）"""
    with open(file_name, encoding="utf-8") as file:
        content = file.readlines()
    return np.mat([line.strip("\n").split(delimiter) for line in content])


# ----------------------------------------------------------------------------
# 一、手算验证：信息熵 / 信息增益（ID3）/ 信息增益率（C4.5）
# ----------------------------------------------------------------------------
def entropy(labels):
    """计算一组标签的信息熵（base=2）"""
    n = len(labels)
    return -sum((c / n) * np.log2(c / n) for c in Counter(labels).values())


def info_gain_and_ratio(data, feat_idx):
    """对离散特征，返回 (信息增益, 分裂信息, 信息增益率)"""
    labels = [str(v) for v in data[:, -1].T.tolist()[0]]
    n = len(labels)
    base_entropy = entropy(labels)
    new_entropy, split_info = 0.0, 0.0
    for value in sorted(set(data[:, feat_idx].T.tolist()[0])):
        idx = np.nonzero(data[:, feat_idx] == value)[0]
        prob = len(idx) / n
        sub_labels = [labels[i] for i in idx]
        new_entropy += prob * entropy(sub_labels)
        split_info -= prob * np.log2(prob)
    gain = base_entropy - new_entropy
    return gain, split_info, gain / split_info


def manual_analysis():
    """手算天气数据集的熵、信息增益与增益率，帮助理解 ID3 与 C4.5 的差别"""
    data = load_dataset(os.path.join(BASE, "data", "weather_nominal.csv"))
    feature_names = ["outlook", "temperature", "humidity", "windy"]
    labels = [str(v) for v in data[:, -1].T.tolist()[0]]

    print("=" * 78)
    print("一、手算验证：信息熵、信息增益（ID3）与信息增益率（C4.5）")
    print("=" * 78)
    print("数据集：weather_nominal.csv，共 %d 个样本，标签 play 的分布：%s"
          % (len(labels), dict(Counter(labels))))
    print("标签的信息熵 Ent(D) = %.4f bit" % entropy(labels))
    print()
    print("%-12s %12s %12s %12s" % ("特征", "信息增益", "分裂信息", "信息增益率"))
    rows = []
    for idx, name in enumerate(feature_names):
        gain, split_info, ratio = info_gain_and_ratio(data, idx)
        rows.append((name, gain, split_info, ratio))
        print("%-12s %12.4f %12.4f %12.4f" % (name, gain, split_info, ratio))

    best_gain = max(rows, key=lambda r: r[1])
    best_ratio = max(rows, key=lambda r: r[3])
    print()
    print("按“信息增益”最大选特征（ID3）  -> %s（增益 %.4f）" % (best_gain[0], best_gain[1]))
    print("按“信息增益率”最大选特征（C4.5）-> %s（增益率 %.4f）" % (best_ratio[0], best_ratio[3]))
    print("说明：ID3 偏向取值多的特征；C4.5 除以“分裂信息”做修正，抑制这种偏好。")

    # 画一张“信息增益 vs 信息增益率”的对比柱状图
    names = [r[0] for r in rows]
    gains = [r[1] for r in rows]
    ratios = [r[3] for r in rows]
    x = np.arange(len(names))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].bar(x, gains, color="#3498db", width=0.55)
    axes[0].set_xticks(x); axes[0].set_xticklabels(names)
    axes[0].set_ylabel("信息增益"); axes[0].set_title("ID3：信息增益", fontsize=11)
    axes[0].grid(alpha=0.3, axis="y")
    for i, v in enumerate(gains):
        axes[0].text(i, v + 0.004, "%.4f" % v, ha="center", fontsize=9)
    axes[1].bar(x, ratios, color="#e67e22", width=0.55)
    axes[1].set_xticks(x); axes[1].set_xticklabels(names)
    axes[1].set_ylabel("信息增益率"); axes[1].set_title("C4.5：信息增益率", fontsize=11)
    axes[1].grid(alpha=0.3, axis="y")
    for i, v in enumerate(ratios):
        axes[1].text(i, v + 0.004, "%.4f" % v, ha="center", fontsize=9)
    fig.suptitle("天气数据集：两种特征选择准则对比", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(IMG_DIR, "task1_特征选择_信息增益与增益率.png")
    fig.savefig(out, dpi=150); plt.close(fig)
    print("已保存：", out)
    return rows


# ----------------------------------------------------------------------------
# 二、使用ID3 / C4.5 代码建树
# ----------------------------------------------------------------------------
def encode_for_sklearn(data):
    """把全离散的字符串数据编码成整数矩阵，供 sklearn 使用；返回 (X, y, 编码表)"""
    n, d = data.shape
    X = np.zeros((n, d - 1), dtype=int)
    mapping = []
    for j in range(d - 1):
        values = sorted(set(data[:, j].T.tolist()[0]))
        mapping.append(dict(zip(values, range(len(values)))))
        for i in range(n):
            X[i, j] = mapping[j][data[i, j]]
    y_values = sorted(set(data[:, -1].T.tolist()[0]))
    y_map = dict(zip(y_values, range(len(y_values))))
    y = np.array([y_map[data[i, -1]] for i in range(n)])
    return X, y, mapping


def evaluate(tree, feature_list, data, name):
    """用决策树对训练集分类，返回预测结果与正确率"""
    y_hat = []
    for i in range(len(data)):
        y_hat.append(str(c45.classify(tree, feature_list, data[i, :-1])
                         if name.startswith("C4.5") else id3.classify(tree, feature_list, data[i, :-1])))
    y_true = [str(v) for v in data[:, -1].T.tolist()[0]]
    acc = float(np.mean(np.array(y_hat) == np.array(y_true)))
    return y_hat, acc


def pretty_tree(tree, indent=0):
    """把字典形式的决策树打印成带缩进的可读文本"""
    if not isinstance(tree, dict):
        return " " * indent + "└─ 叶节点：" + str(tree)
    key = list(tree.keys())[0]
    lines = [" " * indent + "├─ 判断特征：" + str(key)]
    for value, sub in tree[key].items():
        lines.append(" " * (indent + 2) + "├─ 取值 %s：" % value)
        lines.append(pretty_tree(sub, indent + 4))
    return "\n".join(lines)


def run_teacher_code():
    print()
    print("=" * 78)
    print("二、调用现有代码：ID3（离散）与 C4.5（含连续特征）")
    print("=" * 78)
    feature_list = ["outlook", "temperature", "humidity", "windy"]

    # --- ID3：只能处理离散特征，用 weather_nominal.csv ---
    data = load_dataset(os.path.join(BASE, "data", "weather_nominal.csv"))
    id3_tree = id3.build_id3_tree(data, feature_list)
    y_hat, acc = evaluate(id3_tree, feature_list, data, "ID3")
    depth, leaves, inner = dt_utils.tree_stats(id3_tree)
    print("[ID3] 数据 weather_nominal.csv（4 个离散特征）")
    print("  树的深度 = %d，叶子数 = %d，内部节点数 = %d" % (depth, leaves, inner))
    print("  训练集分类正确率 = %.2f%%" % (acc * 100))
    print("  决策树结构（缩进文本）：")
    print(pretty_tree(id3_tree, 4))
    dt_utils.plot_dict_tree(id3_tree, os.path.join(IMG_DIR, "task1_ID3决策树_天气数据.png"),
                            "ID3 决策树（weather_nominal.csv）")
    with open(os.path.join(IMG_DIR, "task1_ID3决策树.dot"), "w", encoding="utf-8") as f:
        f.write(dt_utils.dict_tree_to_dot(id3_tree))

    # --- C4.5：能处理连续特征，用 weather_numeric.csv ---
    data_num = load_dataset(os.path.join(BASE, "data", "weather_numeric.csv"))
    with quiet():
        c45_tree = c45.build_c45_tree(data_num, feature_list)
    y_hat45, acc45 = evaluate(c45_tree, feature_list, data_num, "C4.5")
    depth45, leaves45, inner45 = dt_utils.tree_stats(c45_tree)
    print()
    print("[C4.5] 数据 weather_numeric.csv（temperature、humidity 为连续特征）")
    print("  树的深度 = %d，叶子数 = %d，内部节点数 = %d" % (depth45, leaves45, inner45))
    print("  训练集分类正确率 = %.2f%%" % (acc45 * 100))
    print("  决策树结构（缩进文本）：")
    print(pretty_tree(c45_tree, 4))
    print("  提示：C4.5 对连续特征会学出形如“humidity <= 某阈值”的分裂点，这是 ID3 做不到的。")
    dt_utils.plot_dict_tree(c45_tree, os.path.join(IMG_DIR, "task1_C45决策树_天气数据.png"),
                            "C4.5 决策树（weather_numeric.csv）")
    with open(os.path.join(IMG_DIR, "task1_C45决策树.dot"), "w", encoding="utf-8") as f:
        f.write(dt_utils.dict_tree_to_dot(c45_tree))

    return id3_tree, c45_tree, data, data_num, feature_list


# ----------------------------------------------------------------------------
# 三、与 sklearn 决策树对比
# ----------------------------------------------------------------------------
def compare_with_sklearn(data, feature_list):
    from sklearn.tree import DecisionTreeClassifier
    print()
    print("=" * 78)
    print("三、与 sklearn 决策树对比（同样用天气数据）")
    print("=" * 78)
    X, y, _ = encode_for_sklearn(data)
    class_names = sorted(set(str(v) for v in data[:, -1].T.tolist()[0]))
    clf = DecisionTreeClassifier(criterion="entropy", random_state=42)
    clf.fit(X, y)
    acc = clf.score(X, y)
    print("sklearn 决策树（criterion=entropy）：深度 = %d，叶子数 = %d，训练集正确率 = %.2f%%"
          % (clf.get_depth(), clf.get_n_leaves(), acc * 100))
    print("说明：sklearn 的决策树是“二叉树”，对多取值特征会拆成多层的 <= 判断；")
    print("      ID3 是“多叉树”，一个特征一次就能分出 outlook 的 3 个取值。")
    dt_utils.plot_sklearn_tree(clf, feature_list, class_names,
                               os.path.join(IMG_DIR, "task1_sklearn决策树_天气数据.png"),
                               "sklearn 决策树（criterion=entropy）")
    dt_utils.export_sklearn_dot(clf, feature_list, class_names,
                                os.path.join(IMG_DIR, "task1_sklearn决策树.dot"))
    return clf


# ----------------------------------------------------------------------------
# 四、熵与 Gini 系数曲线（与 plot_entropy_gini.py 一致）
# ----------------------------------------------------------------------------
def plot_entropy_gini():
    x = np.linspace(0.001, 0.999, 400)
    entropy_curve = -x * np.log2(x) - (1 - x) * np.log2(1 - x)
    gini_curve = 1 - (x ** 2 + (1 - x) ** 2)
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.plot(x, entropy_curve / 2, "--", label="熵之半 H(p)/2", color="#3498db")
    ax.plot(x, gini_curve, ":", label="Gini 系数 Gini(p)", color="#e67e22")
    ax.set_xlabel("正类样本比例 p"); ax.set_ylabel("不纯度")
    ax.set_title("二分类问题的不纯度曲线：熵与 Gini 系数", fontsize=12)
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    out = os.path.join(IMG_DIR, "task1_熵与Gini系数.png")
    fig.savefig(out, dpi=150); plt.close(fig)
    print()
    print("=" * 78)
    print("四、熵与 Gini 系数")
    print("=" * 78)
    print("两者都在 p=0.5 时最大、在 p=0 或 1 时为 0，且 Gini 恒不超过熵之半；")
    print("ID3/C4.5 用熵，CART 用 Gini 系数，本质都是“让子节点尽可能纯”。")
    print("已保存：", out)


def main():
    manual_analysis()
    run_teacher_code()
    data = load_dataset(os.path.join(BASE, "data", "weather_nominal.csv"))
    compare_with_sklearn(data, ["outlook", "temperature", "humidity", "windy"])
    plot_entropy_gini()
    print()
    print("任务1 运行完毕，所有图片与 .dot 文件都在：", IMG_DIR)


if __name__ == "__main__":
    main()
