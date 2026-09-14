# 实验三 数据集说明

本文件夹存放实验三（决策树）用到的数据集。

| 文件 | 说明 | 用途 |
| --- | --- | --- |
| `weather_nominal.csv` | 经典“打网球（Play Tennis）”天气数据集，14 个样本、4 个**离散**特征（outlook、temperature、humidity、windy），标签为 play（yes/no） | 任务 1：验证 ID3 算法（ID3 只能处理离散特征） |
| `weather_numeric.csv` | 与上面同一批样本，但把 temperature（华氏度）和 humidity（百分比）改成了**连续数值**，outlook、windy 仍为离散取值 | 任务 1：验证 C4.5 算法（C4.5 能同时处理离散与连续特征） |
| `seeds_dataset.txt` | 课程提供的 UCI 小麦种子数据集（Seeds），210 个样本、7 个连续特征、3 个类别（Kama / Rosa / Canadian），制表符分隔，最后一列是类别编号 1/2/3 | 任务 2：用纯 Python 决策树代码对种子数据集分类 |

说明：
- `weather_nominal.csv` / `weather_numeric.csv` 的样本完全对应，便于对比 ID3 与 C4.5 在同一问题上的差异；
  C4.5 会把连续特征按“信息增益率最大”的分裂点二分成 `<=` 与 `>` 两支。
- `seeds_dataset.txt` 与实验二中使用的是同一份课程提供的数据集，这里复制到实验三目录下，使实验三可以独立运行。
- 任务 3 使用的自选数据集为 `sklearn` 自带数据（分类用 wine 葡萄酒数据集、回归用 diabetes 糖尿病数据集），
  随 scikit-learn 一起安装、无需联网下载。
