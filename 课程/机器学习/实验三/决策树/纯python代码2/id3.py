# -*- coding: utf-8 -*-
"""
实现Quinlan的ID3决策树算法

The Elements of Machine Learning ---- Principles Algorithms and Practices(Python Edition)
@author: Mike Yuan, Copyright 2019~2020
"""

import numpy as np
from collections import Counter


def calc_entropy(data_set):
    """
    计算最后一列（标签）的信息熵
    输入参数
        data_set：数据集
    输出参数
        entropy：熵
    """
    n, d = data_set.shape
    entropy = 0.
    # 最后一列是标签
    label_set = set(data_set[:, -1].T.tolist()[0])
    for label in label_set:
        occurrence_num = len(data_set[np.nonzero(data_set[:, -1] == label)[0], :])
        prob = float(occurrence_num) / n  # 换算为概率
        entropy -= prob * np.log2(prob)
    return entropy


def split_dataset(data_set, feat_idx, value):
    """
    按照给定特征划分数据集
    输入参数
        data_set：数据集，feat_idx：给定的特征序号, value：值
    输出参数
        ret_data：满足条件的划分数据集
    """
    result_data = data_set[np.nonzero(data_set[:, feat_idx] == value)[0], :]
    # ID3算法用过一个特征，就不能再用
    ret_data = np.delete(result_data, feat_idx, axis=1)
    return ret_data


def choose_best_feature(data_set):
    """
    选择最佳的分裂特征
    输入参数
        data_set：数据集
    输出参数
        best_feature：最佳的分裂特征索引
    """
    n, d = data_set.shape
    base_entropy = calc_entropy(data_set)  # 标签信息熵
    best_info_gain = 0.
    best_feature = -1
    for idx in range(d - 1):  # 不计标签
        new_entropy = 0.
        # 不重复的特征取值
        feat_value = sorted(set(data_set[:, idx].T.tolist()[0]))
        # 计算每种特征取值的信息熵
        for value in feat_value:
            sub_data = split_dataset(data_set, idx, value)
            prob = sub_data.shape[0] / float(n)
            new_entropy += prob * calc_entropy(sub_data)
        # 计算最佳信息增益
        info_gain = base_entropy - new_entropy
        if info_gain > best_info_gain:
            best_info_gain = info_gain
            best_feature = idx
    return best_feature


def majority_label(data_set):
    """
    返回叶子节点出现次数最多的类别标签
    输入参数
        data_set：数据集
    输出参数
        major_label：最多的类别标签
    """
    major_label = Counter(data_set[:, -1].T.tolist()[0]).most_common(1)[0][0]
    return major_label


def build_id3_tree(data_set, feature_list):
    """
    创建ID3决策树
    输入参数
        data_set：数据集，feature_list：特征名称列表
    输出参数
        my_tree：创建的决策树
    """
    _feat_list = feature_list.copy()    # 复制一份，以免后面del引起改变
    if data_set is None:
        raise ValueError('数据为空错误。')
    if len(set(data_set[:, -1].T.tolist()[0])) == 1:
        # 类别完全相同，停止划分
        return data_set[0, -1]
    if data_set.shape[1] == 1 or len(data_set) <= 3:
        # 没有可用属性 or 样本太少
        return majority_label(data_set)
    best_feat = choose_best_feature(data_set)  # 最佳分裂特征

    best_feat_name = _feat_list[best_feat]
    del _feat_list[best_feat]     # 删除特征列表中使用过的特征名称
    my_tree = {best_feat_name: {}}

    # 特征的不重复取值
    feat_value = sorted(set(data_set[:, best_feat].T.tolist()[0]))
    for value in feat_value:
        sub_feats = _feat_list[:]
        sub_data = split_dataset(data_set, best_feat, value)
        # 递归创建子树
        my_tree[best_feat_name][value] = build_id3_tree(sub_data, sub_feats)
    return my_tree


def classify(my_tree, feature_list, test_vec):
    """
    使用决策树分类
    输入参数
        my_tree：决策树，feature_list：特征名称列表，test_vec：一条测试数据
    输出参数
        second_dict[key]：分类结果
    """
    first_key = list(my_tree.keys())[0]
    second_dict = my_tree[first_key]

    feat_index = feature_list.index(first_key)
    for key in second_dict.keys():
        if test_vec[0, feat_index] == key:
            if type(second_dict[key]).__name__ == 'dict':
                return classify(second_dict[key], feature_list, test_vec)
            else:
                return second_dict[key]

