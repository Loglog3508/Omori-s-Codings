# -*- coding: utf-8 -*-
"""
K均值算法示例2
应用K-Means算法来压缩图像
原理为：先对图像的每个像素运行K-Means算法，然后将每个像素映射为最近的质心

The Elements of Machine Learning ---- Principles Algorithms and Practices(Python Edition)
@author: Mike Yuan, Copyright 2019~2020
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mp
import matplotlib as mpl
import kmeans_utils

# 防止plt汉字乱码
mpl.rcParams['font.sans-serif'] = ['simhei']
mpl.rcParams['axes.unicode_minus'] = False


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
    plt.legend()


def main():
    np.random.seed(123)
    # 第一步，对图像数据运行K-Means算法
    # 可以尝试修改如下的K值及最大迭代次数max_iters
    k = int(input('请输入K值（2~16）：'))
    max_iters = int(input('请输入最大迭代次数（10~50）：'))

    # 加载图像文件
    img = mp.imread('child.png')

    # 图像尺寸
    img_size = img.shape

    # 重新调整图像数据为Nx3矩阵，N为像素数目。每行有三列，分别为RGB三色
    x = np.reshape(img, (img_size[0] * img_size[1], 3))

    # 随机选择初始质心
    initial_centroids = kmeans_utils.init_centroids(x, k)

    j_values = np.zeros(max_iters)

    # 保存质心历史
    centroids = np.zeros((max_iters + 1, k, len(x[0])))
    centroids[0] = initial_centroids

    # 迭代运行K-Means算法
    for i in range(max_iters):
        # 输出迭代次数
        print('K-Means迭代次数：%d/%d...\n' % (i + 1, max_iters))

        # 将数据集中的每一个样本分配给离它最近的质心
        r, j_values[i] = kmeans_utils.e_step(x, centroids[i])

        # 计算新质心
        centroids[i + 1] = kmeans_utils.m_step(x, r, k)

    # 第二步，图像压缩
    # 最近的质心
    new_r = r

    # 压缩的实质是：将原始图像数据X用质心来表示
    # 因此，将每个像素映射为质心颜色值
    x_recovered = centroids[-1, new_r, :]
    # 重新调整矩阵为适合的图像尺寸
    x_recovered = np.reshape(x_recovered, (img_size[0], img_size[1], 3))

    # 显示原始图像
    plt.subplot(1, 2, 1)
    plt.imshow(img)
    plt.axis('off')
    plt.title(u'原始图像')

    # 显示压缩图像
    plt.subplot(1, 2, 2)
    plt.imshow(x_recovered)
    plt.axis('off')
    plt.title(f'压缩图像({k}色)')

    plt.show()

    # 保存压缩图像
    mp.imsave('compressedchild.png', x_recovered, format='png')

    print('\nK-Means运行完毕。\n\n')


if __name__ == "__main__":
    main()
