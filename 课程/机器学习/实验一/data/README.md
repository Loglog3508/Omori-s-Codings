# 实验一数据文件说明

本文件夹存放机器学习实验一（逻辑回归）所使用到的数据集，均从 sklearn 内置数据集导出为 CSV 格式（UTF-8 带 BOM，可直接用 Excel 打开）。最后一列 `class` 为目标类别编号，`class_name` 为类别名称。

| 文件名 | 数据集 | 样本数 | 特征数 | 类别数 | 类别 |
| --- | --- | --- | --- | --- | --- |
| wine.csv | 红酒数据集（Wine） | 178 | 13 | 3 | class_0 / class_1 / class_2 |
| iris.csv | 鸢尾花数据集（Iris） | 150 | 4 | 3 | setosa / versicolor / virginica |
| breast_cancer.csv | 乳腺癌数据集（Breast Cancer） | 569 | 30 | 2 | malignant（恶性）/ benign（良性） |

## 对应任务
- `wine.csv`	→ 实验任务 3：用纯 Python 代码 1（梯度下降逻辑回归）对红酒数据集分类
- `iris.csv`	→ 实验任务 4：用纯 Python 代码 2（牛顿法逻辑回归）对鸢尾花数据集分类
- `breast_cancer.csv` → 实验任务 5：自选数据集，用逻辑回归解决乳腺癌二分类问题

运行各任务脚本时，直接使用 sklearn 的 `load_wine()` / `load_iris()` / `load_breast_cancer()` 会重新从内置数据加载；如需改为读取本文件夹的 CSV，可将对应脚本中的 `load_*()` 替换为 `pd.read_csv("data/xxx.csv")`。