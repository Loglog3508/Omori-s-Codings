# 实验二数据文件说明

本文件夹存放机器学习实验二（聚类 / K-Means）所使用到的数据集，均为 UTF-8 带 BOM 的 CSV，可直接用 Excel 打开。

| 文件名 | 数据集 | 样本数 | 特征数 | 类别数 | 说明 |
| --- | --- | --- | --- | --- | --- |
| seeds.csv | 小麦种子数据集（UCI Seeds） | 210 | 7 | 3 | 类别为 Kama / Rosa / Canadian 三个小麦品种，每类 70 个 |
| digits.csv | 手写数字数据集（sklearn digits） | 1797 | 64 | 10 | 类别为数字 0~9，每个数字约 180 个样本 |

## seeds.csv 字段

| 列名 | 含义 |
| --- | --- |
| Area | 籽粒面积 |
| Perimeter | 籽粒周长 |
| Compactness | 紧密度 C = 4πA / P² |
| Kernel_Length | 籽粒长度 |
| Kernel_Width | 籽粒宽度 |
| Asymmetry | 不对称系数 |
| Groove_Length | 腹沟长度 |
| class | 类别编号（1 = Kama，2 = Rosa，3 = Canadian） |
| class_name | 类别名称 |

## digits.csv 字段

- `pixel_0` ~ `pixel_63`：每张 8×8 手写数字图片按行展平后的 64 个灰度像素值（取值 0~16）。
- `class`：真实数字标签（0~9）。
- `class_name`：真实数字标签的字符串形式。

## 对应任务

- `seeds.csv`  → 实验任务 2：用纯 Python 代码（自实现 K-Means）对种子数据集进行聚类。
- `digits.csv` → 实验任务 3：自选数据集，用 K-Means 算法解决手写数字聚类问题。

## 数据来源

- Seeds 数据集：UCI Machine Learning Repository，*Seeds* 数据集（210 条记录）。
- Digits 数据集：`sklearn.datasets.load_digits()` 内置数据，导出为 CSV 便于离线使用。