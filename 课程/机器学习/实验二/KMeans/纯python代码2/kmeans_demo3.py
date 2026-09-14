# -*- coding: utf-8 -*-
"""
K均值算法示例3
绘制K与J关系，选择K值

The Elements of Machine Learning ---- Principles Algorithms and Practices(Python Edition)
@author: Mike Yuan, Copyright 2019~2020
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import kmeans_utils

# 防止plt汉字乱码
mpl.rcParams['font.sans-serif'] = ['simhei']
mpl.rcParams['axes.unicode_minus'] = False


def get_data():
    """ 随机生成样本集 """
    m1 = [0, 0]
    m2 = [5, 4]
    s1 = np.eye(2)
    s2 = [[1.0, 0.2], [0.2, 2.5]]
    n = 100
    x1 = np.random.multivariate_normal(m1, s1, n)
    x2 = np.random.multivariate_normal(m2, s2, n)
    x = np.row_stack((x1, x2))
    return x


def plot_kj(kj):
    """
    绘制KJ关系轨迹
    """
    plt.figure()
    plt.plot(np.arange(1, len(kj) + 1), kj, 'b-')
    plt.xlabel('K')
    plt.ylabel('J')
    plt.title(u'KJ关系轨迹')
    # plt.xlim([1, len(kj)])

    plt.show()


def main():
    # K-Means聚类
    print('\n即将运行K-Means聚类算法。\n\n')

    # 随机生成样本集
    np.random.seed(1234)
    x = get_data()

    # 运行K-Means算法所需参数。可尝试更改这些参数并观察其影响
    max_iters = 20
    max_k = 10
    kj = np.zeros(max_k)


    # 迭代运行K-Means算法
    for k in range(1, max_k + 1):
        # 随机选择初始质心
        initial_centroids = kmeans_utils.init_centroids(x, k)

        j_values = np.zeros(max_iters)

        # 运行K-Means算法
        # 保存质心
        centroids = initial_centroids

        for i in range(max_iters):
            # 输出迭代次数
            print('K-Means迭代次数：%d/%d...\n' % (i + 1, max_iters))

            # 将数据集中的每一个样本分配给离它最近的质心
            r, j_values[i] = kmeans_utils.e_step(x, centroids)

            # 计算新质心
            centroids = kmeans_utils.m_step(x, r, k)

            # 如果J不再变化，可以认为已经收敛，退出循环
            if i != 1 and j_values[i] == j_values[i - 1]:
                print(f'已经收敛，迭代次数：{i}\n\n')
                j_values[-1] = j_values[i]
                break

        kj[k - 1] = j_values[-1]

    # 绘制KJ历史轨迹
    plot_kj(kj)

    print('\nK-Means运行完毕。\n\n')


if __name__ == "__main__":
    main()
