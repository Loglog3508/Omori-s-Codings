# 实验一数据文件说明

本文件夹存放机器学习实验一（逻辑回归）中**任务 5 自选数据集**，UTF-8 带 BOM，可直接用 Excel 打开。
最后一列 `class` 为目标类别编号，`class_name` 为类别名称。

| 文件名 | 数据集 | 样本数 | 特征数 | 类别数 | 类别 |
| --- | --- | --- | --- | --- | --- |
| breast_cancer.csv | 乳腺癌数据集（Breast Cancer） | 569 | 30 | 2 | malignant（恶性）/ benign（良性） |

## 对应任务
- `breast_cancer.csv` → 实验任务 5：自选数据集，用逻辑回归解决乳腺癌二分类问题。

## 其他数据集（任务 3、任务 4）
任务 3、任务 4 使用**老师提供**的数据，不在本文件夹，而在：

- `../纯python代码1/wine.data`：红酒数据集（130 个样本、13 个特征、2 类），供任务 3 使用。
- `../纯python代码2/data.txt`：训练数据（200 个样本、2 个特征、带 0/1 标签），供任务 4 使用。
- `../纯python代码2/test_data`：测试数据（200 个样本、2 个特征、无标签），供任务 4 使用。

运行任务 5 的脚本时，直接使用 sklearn 的 `load_breast_cancer()` 会重新从内置数据加载；
如需改为读取本文件夹的 CSV，可将脚本中的 `load_breast_cancer()` 替换为 `pd.read_csv("data/breast_cancer.csv")`。