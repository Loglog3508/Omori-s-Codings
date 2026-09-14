# -*- coding: utf-8 -*-
"""
实现CART决策树算法

The Elements of Machine Learning ---- Principles Algorithms and Practices(Python Edition)
@author: Mike Yuan, Copyright 2019~2020
"""

import numpy as np
from collections import Counter


def calc_gini(data_set):
    """
    计算最后一列（标签）的Gini系数
    输入参数
        data_set：数据集
    输出参数
        gini：Gini系数
    """
    n, d = data_set.shape
    gini = 1.
    # 最后一列是标签
    label_set = set(data_set[:, -1].T.tolist()[0])
    for label in label_set:
        occurrence_num = len(data_set[np.nonzero(data_set[:, -1] == label)[0], :])
        prob = float(occurrence_num) / n  # 换算为概率
        gini -= prob ** 2
    return gini


def split_discrete_dataset(data_set, feat_idx, value):
    """
    按照给定离散特征划分数据集
    输入参数
        data_set：数据集，feat_idx：给定的特征序号, value：取值序号列表
    输出参数
        ret_data：满足条件的划分数据集
    """
    # 不重复的特征取值
    feat_value = sorted(set(data_set[:, feat_idx].T.tolist()[0]))
    target_value = [feat_value[i] for i in value]
    result_data = data_set[np.nonzero(data_set[:, feat_idx] == target_value[0])[0], :]
    if len(target_value) > 1:
        for i in range(1, len(target_value)):
            next_ds = data_set[np.nonzero(data_set[:, feat_idx] == target_value[i])[0], :]
            result_data = np.row_stack((result_data, next_ds))
    return result_data


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
    base_entropy = calc_gini(data_set)  # 标签信息熵
    best_gini_split = 0.
    best_split_point = 0.
    best_left = []
    best_right = []
    best_feature = -1
    for idx in range(d - 1):  # 不计标签
        if is_discrete_feature(data_set, idx):
            # 离散类型
            # 不重复的特征取值
            feat_value = sorted(set(data_set[:, idx].T.tolist()[0]))
            left, right = combination(feat_value)
            # 计算每种特征取值的信息熵
            for i in range(len(left)):
                left_value = left[i]
                right_value = right[i]
                left_data = split_discrete_dataset(data_set, idx, left_value)
                right_data = split_discrete_dataset(data_set, idx, right_value)
                left_prob = left_data.shape[0] / float(n)
                right_prob = right_data.shape[0] / float(n)
                new_gini = left_prob * calc_gini(left_data) + right_prob * calc_gini(right_data)
                # 计算差异性损失
                gini_split = base_entropy - new_gini
                # 更新最佳差异性损失
                if gini_split > best_gini_split:
                    best_gini_split = gini_split
                    best_feature = idx
                    best_split_point = 0.
                    best_left = left_value
                    best_right = right_value
        else:
            # 连续类型
            continuous_feat = data_set[:, idx].astype(float)
            distinct_feat_value = sorted(set(continuous_feat.T.tolist()[0]))
            # 确定测试上下界，跳过两端数据
            # low_bound = 1 if np.sum(continuous_feat[:, 0] == distinct_feat_value[0]) == 1 else 0
            # -2是因为分裂点右边不能只有一个样本
            # high_bound = len(distinct_feat_value) - \
            #              (2 if np.sum(continuous_feat[:, 0] == distinct_feat_value[-1]) == 1 else 1)
            low_bound = 0
            high_bound = len(distinct_feat_value) - 1
            for i in range(low_bound, high_bound):
                left_data, right_data = split_continuous_dataset(data_set, idx, distinct_feat_value[i])
                left_prob = left_data.shape[0] / float(n)
                right_prob = right_data.shape[0] / float(n)
                new_gini = left_prob * calc_gini(left_data) + right_prob * calc_gini(right_data)
                # 计算差异性损失
                gini_split = base_entropy - new_gini
                # 更新最佳差异性损失
                if gini_split > best_gini_split:
                    best_gini_split = gini_split
                    best_feature = idx
                    best_split_point = distinct_feat_value[i]
                    best_left = []
                    best_right = []

    return best_feature, best_split_point, best_left, best_right


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


def combination(bins):
    """
    返回离散属性二分支取值的组合
    输入参数
        bins：离散属性取值数量
    输出参数
        left、right：左右分支可能的组合
    """
    length = len(bins)
    if length == 2:
        left = [[0]]
        right = [[1]]
    elif length == 3:
        left = [[0], [1], [2]]
        right = [[1, 2], [0, 2], [0, 1]]
    elif length == 4:
        left = [[0], [1], [2], [3], [0, 1], [0, 2], [0, 3]]
        right = [[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2], [2, 3], [1, 3], [1, 2]]
    elif length == 5:
        left = [[0], [1], [2], [3], [4], [0, 1], [0, 2], [0, 3], [0, 4]]
        right = [[1, 2, 3, 4], [0, 2, 3, 4], [0, 1, 3, 4], [0, 1, 2, 4], [0, 1, 2, 3], [2, 3, 4],
                 [1, 3, 4], [1, 2, 4], [1, 2, 3]]
    else:
        raise ValueError('错误，分箱数必须在2~5范围内。')
    return left, right


def build_cart_tree(data_set, feature_list):
    """
    创建CART决策树
    注意：本程序没有实现回归树和后剪枝，离散属性取值数目不要超过5
    输入参数
        data_set：数据集，feature_list：特征名称列表
    输出参数
        my_tree：创建的决策树
    """
    _feat_list = feature_list.copy()  # 复制一份，以免后面del操作改变原值
    if data_set is None:
        raise ValueError('数据为空错误。')
    if len(set(data_set[:, -1].T.tolist()[0])) == 1:
        # 类别完全相同，停止划分
        return data_set[0, -1]
    if data_set.shape[1] == 1 or len(data_set) <= 3:
        # 没有可用属性 or 样本太少
        return majority_label(data_set)
    best_feat, best_split_point, best_left, best_right = choose_best_feature(data_set)  # 最佳分裂特征

    best_feat_name = _feat_list[best_feat]
    if is_discrete_feature(data_set, best_feat):
        # 离散特征处理
        my_tree = {best_feat_name: {}}

        # 特征的不重复取值
        feat_value = sorted(set(data_set[:, best_feat].T.tolist()[0]))
        # 左右分支
        left_data = split_discrete_dataset(data_set, best_feat, best_left)
        right_data = split_discrete_dataset(data_set, best_feat, best_right)
        # 递归创建左右子树
        sub_feats = _feat_list[:]
        left_label = '|'.join([feat_value[i] for i in best_left])
        right_label = '|'.join([feat_value[i] for i in best_right])
        my_tree[best_feat_name][f'={left_label}'] = build_cart_tree(left_data, sub_feats)
        sub_feats = _feat_list[:]
        my_tree[best_feat_name][f'={right_label}'] = build_cart_tree(right_data, sub_feats)

    else:
        # 连续特征处理
        my_tree = {best_feat_name: {}}
        # 左右分支
        left_data, right_data = split_continuous_dataset(data_set, best_feat, best_split_point)
        # 递归创建左右子树
        sub_feats = _feat_list[:]
        my_tree[best_feat_name][f'<={best_split_point}'] = build_cart_tree(left_data, sub_feats)
        sub_feats = _feat_list[:]
        my_tree[best_feat_name][f'>{best_split_point}'] = build_cart_tree(right_data, sub_feats)

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
            if key.find(test_vec[0, feat_index]) != -1:
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
