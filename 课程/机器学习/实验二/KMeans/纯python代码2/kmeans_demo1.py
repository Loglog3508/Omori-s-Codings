# -*- coding: utf-8 -*-
"""
K均值算法示例1

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


def plot_centroids_history(x, centroids, r, k, iters):
    """
    绘制K均值运行过程，只能用于二维数据
    输入
        x：数据集
        centroids：质心
        r：样本隶属的质心
        k：质心数
        iters：已运行的迭代次数
    输出
        无
    """
    plt.clf()
    filled_markers = ('o', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd', 'P', 'X')
    # 绘制样本散点图
    for c in range(k):
        plt.scatter(x[np.where(r == c), 0], x[np.where(r == c), 1], marker=filled_markers[c], alpha=0.5,
                    label=f'簇{c}')

    # 绘制质心的历史轨迹
    for i in range(iters + 1):
        plt.plot(centroids[i, :, 0], centroids[i, :, 1], 'rx', ms=10)
        if i != 0:
            for c in range(k):
                plt.plot([centroids[i - 1, c, 0], centroids[i, c, 0]], [centroids[i - 1, c, 1], centroids[i, c, 1]])
    plt.title(f'迭代次数：{iters + 1}')
    plt.xlabel('x1')
    plt.ylabel('x2')
    plt.legend(loc='upper left')


def plot_jhistory(j_history):
    """
    绘制代价J的下降曲线
    输入参数：
        Jhistory：J历史
    返回：
        无
    """
    plt.figure()
    plt.plot(np.arange(1, len(j_history) + 1), j_history, 'b-')  # 绘制J历史曲线
    plt.xlabel(u'迭代次数')
    plt.ylabel(u'代价J')
    plt.title(u'J历史')

    plt.show()


def main():
    # K-Means聚类
    print('\n即将运行K-Means聚类算法。\n\n')

    # 随机生成样本集
    np.random.seed(1234)
    x = get_data()

    # 运行K-Means算法所需参数。可尝试更改这些参数并观察其影响
    k = 2
    max_iters = 8

    # 随机选择初始质心
    # initial_centroids = kmeans_utils.init_centroids(x, k)
    # 固定选择初始质心
    initial_centroids = np.array([[5, -1], [0, 6]])

    j_values = np.zeros(max_iters)

    # 保存质心历史
    centroids = np.zeros((max_iters + 1, k, len(x[0])))
    centroids[0] = initial_centroids

    # 迭代运行K-Means算法
    plt.figure()
    # 打开交互模式
    plt.ion()
    for i in range(max_iters):
        # 输出迭代次数
        print('K-Means迭代次数：%d/%d...\n' % (i + 1, max_iters))

        # 将数据集中的每一个样本分配给离它最近的质心
        r, j_values[i] = kmeans_utils.e_step(x, centroids[i])

        # 绘制聚类进度
        plot_centroids_history(x, centroids, r, k, i)
        plt.pause(1)

        # 计算新质心
        centroids[i + 1] = kmeans_utils.m_step(x, r, k)

    # 关闭交互模式
    plt.ioff()
    plt.show()

    # 绘制J历史轨迹
    plot_jhistory(j_values)
    print('\nK-Means运行完毕。\n\n')


if __name__ == "__main__":
    main()
