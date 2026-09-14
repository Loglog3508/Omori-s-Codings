# -*- coding: utf-8 -*-
"""
绘制熵和Gini系数

The Elements of Machine Learning ---- Principles Algorithms and Practices(Python Edition)
@author: Mike Yuan, Copyright 2019~2020
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# 防止plt汉字乱码
mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False


def main():
    x = np.linspace(0, 1)
    eps = 1e-6
    entropy = -x * np.log2(x + eps) - (1 - x) * np.log2(1 - x + eps)
    gini = 1 - (x ** 2 + (1 - x) ** 2)
    plt.figure()
    plt.plot(x, entropy / 2, '--')
    plt.plot(x, gini, ':')
    plt.legend([u'熵之半', u'Gini系数'])
    plt.show()


if __name__ == "__main__":
    main()
