# -*- coding: utf-8 -*-
"""
实验三（决策树）公共工具模块

把三个任务脚本都要用到的“画决策树 / 树信息统计 / 导出 DOT / 评价指标”等代码集中在这里，
避免在每个任务脚本里重复实现。本模块只依赖 numpy 和 matplotlib。

主要函数：
    plot_dict_tree(tree, filename, title)   —— 绘制现有代码返回的“字典形式”决策树
    dict_tree_to_dot(tree)                  —— 把字典形式的决策树转成 Graphviz DOT 文本
    tree_stats(tree)                        —— 统计字典形式决策树的深度、叶子数
    plot_sklearn_tree(...)                  —— 绘制 sklearn 决策树
    export_sklearn_dot(...)                 —— 把 sklearn 决策树导出为 .dot 文件
    classification_metrics(y_true, y_pred)  —— 计算准确率、宏平均精确率/召回率/F1
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

# 防止图中汉字乱码
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
matplotlib.rcParams["axes.unicode_minus"] = False


# ----------------------------------------------------------------------------
# 一、现有代码返回的“字典形式”决策树：统计与绘制
# ----------------------------------------------------------------------------
def _to_nodes(tree, depth, nodes):
    """把嵌套字典形式的决策树展开成节点列表，返回当前节点的 id"""
    idx = len(nodes)
    node = {"id": idx, "depth": depth, "label": None, "children": []}
    nodes.append(node)
    if isinstance(tree, dict):
        key = list(tree.keys())[0]
        node["label"] = str(key)
        for value, sub_tree in tree[key].items():
            child_id = _to_nodes(sub_tree, depth + 1, nodes)
            node["children"].append((str(value), child_id))
    else:
        node["label"] = str(tree)
    return idx


def tree_stats(tree):
    """返回 (深度, 叶子数, 内部节点数)"""
    nodes = []
    _to_nodes(tree, 0, nodes)
    depth = max((n["depth"] for n in nodes), default=0)
    leaves = sum(1 for n in nodes if not n["children"])
    inner = len(nodes) - leaves
    return depth, leaves, inner


def plot_dict_tree(tree, filename, title="决策树", figsize=None):
    """绘制字典形式的决策树（用于课程提供的 ID3 / C4.5 / CART 代码输出）"""
    nodes = []
    _to_nodes(tree, 0, nodes)
    if not nodes:
        return

    # 用“叶子节点从左到右编号、内部节点取子节点横坐标均值”的方式布局
    xs = {}
    leaf_counter = [0]

    def assign(idx):
        node = nodes[idx]
        if not node["children"]:
            xs[idx] = leaf_counter[0]
            leaf_counter[0] += 1
        else:
            for _, child_id in node["children"]:
                assign(child_id)
            xs[idx] = float(np.mean([xs[c] for _, c in node["children"]]))

    assign(0)
    ys = {n["id"]: -n["depth"] for n in nodes}

    if figsize is None:
        width = max(6.0, 1.4 * (leaf_counter[0] + 1))
        height = max(3.0, 1.5 * (max(ys.values()) * -1 + 2))
        figsize = (width, height)
    fig, ax = plt.subplots(figsize=figsize)

    # 先画连线
    for node in nodes:
        for edge_label, child_id in node["children"]:
            ax.plot([xs[node["id"]], xs[child_id]], [ys[node["id"]], ys[child_id]],
                    "-", color="#7f8c8d", lw=1.1, zorder=1)
            ax.text((xs[node["id"]] + xs[child_id]) / 2.0,
                    (ys[node["id"]] + ys[child_id]) / 2.0 + 0.06,
                    edge_label, fontsize=8, color="#c0392b", ha="center",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))

    # 再画节点
    for node in nodes:
        x, y = xs[node["id"]], ys[node["id"]]
        is_leaf = not node["children"]
        color = "#2ecc71" if is_leaf else "#3498db"
        ax.scatter([x], [y], s=1500, c=color, alpha=0.85, zorder=2,
                   edgecolors="white", linewidths=1.5)
        ax.text(x, y, node["label"], fontsize=9, ha="center", va="center",
                color="white", zorder=3, fontweight="bold")

    ax.set_title(title, fontsize=13, pad=12)
    ax.axis("off")
    ax.margins(x=0.06, y=0.12)
    fig.tight_layout()
    fig.savefig(filename, dpi=150, bbox_inches="tight")
    plt.close(fig)


def dict_tree_to_dot(tree, node_name="n"):
    """把字典形式的决策树转成 Graphviz DOT 文本（可用 Graphviz 渲染）"""
    lines = ["digraph Tree {",
             "    node [shape=box, style=filled,rounded, color=black];",
             "    edge [fontname=Microsoft YaHei];"]
    counter = [0]

    def walk(sub_tree, parent=None, edge_label=None):
        counter[0] += 1
        name = "%s%d" % (node_name, counter[0])
        if isinstance(sub_tree, dict):
            key = list(sub_tree.keys())[0]
            lines.append('    %s [label="%s", fillcolor="#3498db", fontcolor="white"];'
                         % (name, str(key).replace('"', "")))
            if parent:
                lines.append('    %s -> %s [label="%s"];' % (parent, name, edge_label))
            for value, child in sub_tree[key].items():
                walk(child, name, str(value))
        else:
            lines.append('    %s [label="%s", fillcolor="#2ecc71", fontcolor="white"];'
                         % (name, str(sub_tree).replace('"', "")))
            if parent:
                lines.append('    %s -> %s [label="%s"];' % (parent, name, edge_label))

    walk(tree)
    lines.append("}")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# 二、sklearn 决策树：绘制与导出
# ----------------------------------------------------------------------------
def plot_sklearn_tree(clf, feature_names, class_names, filename, title="决策树", figsize=None):
    """用 sklearn.tree.plot_tree 绘制决策树"""
    from sklearn.tree import plot_tree
    depth = clf.get_depth()
    if figsize is None:
        figsize = (max(8.0, 2.6 * (depth + 1)), max(5.0, 1.5 * (depth + 1)))
    cn = None if class_names is None else [str(c) for c in class_names]
    fig, ax = plt.subplots(figsize=figsize)
    plot_tree(clf, feature_names=feature_names, class_names=cn,
              filled=True, rounded=True, fontsize=8, ax=ax)
    ax.set_title(title, fontsize=13, pad=12)
    fig.tight_layout()
    fig.savefig(filename, dpi=150, bbox_inches="tight")
    plt.close(fig)


def export_sklearn_dot(clf, feature_names, class_names, dot_path):
    """把 sklearn 决策树导出成 .dot 文件（export_graphviz 本身不需要安装 Graphviz 程序）"""
    from sklearn.tree import export_graphviz
    cn = None if class_names is None else [str(c) for c in class_names]
    with open(dot_path, "w", encoding="utf-8") as f:
        export_graphviz(clf, out_file=f, feature_names=feature_names,
                        class_names=cn, filled=True, rounded=True)
    return dot_path


def try_render_dot(dot_path, png_path):
    """若本机安装了 Graphviz，则把 .dot 渲染成 png；否则返回 False（不影响实验其它部分）"""
    try:
        import graphviz
        src = graphviz.Source.from_file(dot_path)
        src.render(filename=os.path.splitext(png_path)[0], format="png", cleanup=True)
        return True
    except Exception:
        return False


# ----------------------------------------------------------------------------
# 三、评价指标
# ----------------------------------------------------------------------------
def classification_metrics(y_true, y_pred):
    """返回 (准确率, 宏平均精确率, 宏平均召回率, 宏平均F1)"""
    from sklearn.metrics import (accuracy_score, precision_score,
                                 recall_score, f1_score)
    return (accuracy_score(y_true, y_pred),
            precision_score(y_true, y_pred, average="macro", zero_division=0),
            recall_score(y_true, y_pred, average="macro", zero_division=0),
            f1_score(y_true, y_pred, average="macro", zero_division=0))
