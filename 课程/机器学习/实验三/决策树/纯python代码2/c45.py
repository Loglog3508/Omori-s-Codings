# -*- coding: utf-8 -*-
"""
实现Quinlan的C4.5决策树算法

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


def split_discrete_dataset(data_set, feat_idx, value):
    """
    按照给定离散特征划分数据集
    输入参数
        data_set：数据集，feat_idx：给定的特征序号, value：值
    输出参数
        ret_data：满足条件的划分数据集
    """
    result_data = data_set[np.nonzero(data_set[:, feat_idx] == value)[0], :]
    # C4.5算法用过一个离散特征，就不能再用
    ret_data = np.delete(result_data, feat_idx, axis=1)
    return ret_data


def split_continuous_dataset(data_set, feat_idx, value):
    """
    按照给定连续特征划分数据集
    输入参数
        data_set：数据集，feat_idx：给定的特征序号, value：值
    输出参数
        left_data，right_data：划分的SL和SR数据集
    """
    left_data = data_set[np.nonzero(data_set[:, feat_idx].astype(float) <= value)[0], :]
    right_data = data_set[np.nonzero(data_set[:, feat_idx].astype(float) > value)[0], :]
    return left_data, right_data


def is_discrete_feature(data_set, feat_idx):
    """
    测试是否为离散属性
    输入参数
        data_set：数据集，feat_idx：给定的特征序号
    输出参数
        is_str_feat：是否为离散属性
    """
    is_str_feat = False
    try:
        _ = data_set[:, feat_idx].astype(float)
    except ValueError:
        is_str_feat = True

    return is_str_feat


def choose_best_feature(data_set):
    """
    选择最佳的分裂特征
    输入参数
        data_set：数据集
    输出参数
        best_feature：最佳的分裂特征索引，best_split_point：最佳的连续属性分裂点
    """
    n, d = data_set.shape
    base_entropy = calc_entropy(data_set)  # 标签信息熵
    best_ig_ratio = 0.
    best_split_point = 0.
    best_feature = -1
    for idx in range(d - 1):  # 不计标签
        new_entropy = 0.
        split_entropy = 0.

        if is_discrete_feature(data_set, idx):
            # 离散类型
            # 不重复的特征取值
            feat_value = sorted(set(data_set[:, idx].T.tolist()[0]))
            # 计算每种特征取值的信息熵
            for value in feat_value:
                sub_data = split_discrete_dataset(data_set, idx, value)
                prob = sub_data.shape[0] / float(n)
                new_entropy += prob * calc_entropy(sub_data)
                split_entropy -= prob * np.log2(prob)
            # 计算信息增益率
            info_gain_ratio = (base_entropy - new_entropy) / split_entropy
            # 更新最佳信息增益率
            if info_gain_ratio > best_ig_ratio:
                best_ig_ratio = info_gain_ratio
                best_feature = idx
                best_split_point = 0.
        else:
            # 连续类型
            continuous_feat = data_set[:, idx].astype(float)
            distinct_feat_value = sorted(set(continuous_feat.T.tolist()[0]))
            # 确定测试上下界，跳过两端数据
            low_bound = 1 if np.sum(continuous_feat[:, 0] == distinct_feat_value[0]) == 1 else 0
            # -2是因为分裂点右边不能只有一个样本
            high_bound = len(distinct_feat_value) - \
                         (2 if np.sum(continuous_feat[:, 0] == distinct_feat_value[-1]) == 1 else 1)
            for i in range(low_bound, high_bound):
                left_data, right_data = split_continuous_dataset(data_set, idx, distinct_feat_value[i])
                left_prob = left_data.shape[0] / float(n)
                right_prob = right_data.shape[0] / float(n)
                new_entropy = left_prob * calc_entropy(left_data) + right_prob * calc_entropy(right_data)
                split_entropy = - left_prob * np.log2(left_prob) - right_prob * np.log2(right_prob)
                # 计算信息增益率
                info_gain_ratio = (base_entropy - new_entropy) / split_entropy
                # 更新最佳信息增益率
                if info_gain_ratio > best_ig_ratio:
                    best_ig_ratio = info_gain_ratio
                    best_feature = idx
                    best_split_point = distinct_feat_value[i]

    return best_feature, best_split_point


def majority_label(data_set):
    """
    返回叶子节点出现次数最多的类别标签
    输入参数
        data_set：数据集
    输出参数
        major_label：最多的类别标签
    """
    print()
    print(data_set)
    major_label = Counter(data_set[:, -1].T.tolist()[0]).most_common(1)[0][0]
    return major_label


def build_c45_tree(data_set, feature_list):
    """
    创建C4.5决策树
    输入参数
        data_set：数据集，feature_list：特征名称列表
    输出参数
        my_tree：创建的决策树
    """
    _feat_list = feature_list.copy()    # 复制一份，以免后面del操作改变原值
    if data_set is None or data_set.size == 0:
        return
        # raise ValueError('数据为空错误。')
    if len(set(data_set[:, -1].T.tolist()[0])) == 1:
        # 类别完全相同，停止划分
        return data_set[0, -1]
    if data_set.shape[1] == 1 or len(data_set) <= 3:
        # 没有可用属性 or 样本太少（3个样本也没法再分）
        return majority_label(data_set)
    best_feat, best_split_point = choose_best_feature(data_set)  # 最佳分裂特征

    best_feat_name = _feat_list[best_feat]
    if is_discrete_feature(data_set, best_feat):
        # 离散特征处理
        del _feat_list[best_feat]  # 删除特征列表中使用过的离散特征名称
        my_tree = {best_feat_name: {}}

        # 特征的不重复取值
        feat_value = sorted(set(data_set[:, best_feat].T.tolist()[0]))
        for value in feat_value:
            sub_feats = _feat_list[:]
            sub_data = split_discrete_dataset(data_set, best_feat, value)
            # 递归创建子树
            my_tree[best_feat_name][value] = build_c45_tree(sub_data, sub_feats)

    else:
        # 连续特征处理
        my_tree = {best_feat_name: {}}
        # 左右分支
        left_data, right_data = split_continuous_dataset(data_set, best_feat, best_split_point)
        # 递归创建左右子树
        sub_feats = _feat_list[:]
        my_tree[best_feat_name][f'<={best_split_point}'] = build_c45_tree(left_data, sub_feats)
        sub_feats = _feat_list[:]
        my_tree[best_feat_name][f'>{best_split_point}'] = build_c45_tree(right_data, sub_feats)

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
    if is_discrete_feature(test_vec, feat_index):
        # 离散属性
        for key in second_dict.keys():
            if test_vec[0, feat_index] == key:
                if type(second_dict[key]).__name__ == 'dict':
                    return classify(second_dict[key], feature_list, test_vec)
                else:
                    return second_dict[key]
    else:
        # 连续属性
        for key in second_dict.keys():
            if key.find('<=') != -1:
                value = float(key[2:])
                if float(test_vec[0, feat_index]) <= value:
                    if type(second_dict[key]).__name__ == 'dict':
                        return classify(second_dict[key], feature_list, test_vec)
                    else:
                        return second_dict[key]
            elif key.find('>') != -1:
                value = float(key[1:])
                if float(test_vec[0, feat_index]) > value:
                    if type(second_dict[key]).__name__ == 'dict':
                        return classify(second_dict[key], feature_list, test_vec)
                    else:
                        return second_dict[key]
            else:
                raise ValueError('决策树格式错误。')