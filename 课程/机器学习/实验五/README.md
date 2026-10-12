# 机器学习 实验五：sklearn 的使用

实验题目：**sklearn 的使用**

## 一、实验目的
- 掌握 sklearn 的基础使用方法、模型选择。
- 掌握交叉验证、数据预处理原理，并能够应用到实际问题中。

## 二、任务清单
| 任务 | 内容 | 对应脚本 |
| --- | --- | --- |
| 任务 1 | 理解文本相关的模型选择与特征抽取（DictVectorizer / CountVectorizer / TfidfVectorizer / train_test_split） | `task1_特征抽取与模型选择.py` |
| 任务 2 | 用 sklearn 实现交叉验证（KFold / cross_val_score / cross_validate / GridSearchCV） | `task2_交叉验证.py` |
| 任务 3 | 用 sklearn 实现数据预处理（StandardScaler / MinMaxScaler / RobustScaler / LabelEncoder / OneHotEncoder） | `task3_数据预处理.py` |

## 三、文件结构
```
实验五/
├── task1_特征抽取与模型选择.py    # 特征抽取：向量化、one-hot、数据集划分
├── task2_交叉验证.py              # KFold / 交叉验证 / 网格搜索 / 多模型对比
├── task3_数据预处理.py            # 缩放器对比、类别编码、缩放对 KNN 的影响
├── 结果图/                        # 运行产生的图片
│   ├── task2_GridSearchCV_决策树深度选择.png
│   ├── task2_多模型交叉验证对比.png
│   └── task3_数据缩放对比.png
└── README.md
```

## 四、运行方法
依赖库：`numpy`、`matplotlib`、`scikit-learn`（以及可选的 `jieba`）。

```powershell
python task1_特征抽取与模型选择.py
python task2_交叉验证.py
python task3_数据预处理.py
```

- 任务 1 的中文分词优先使用 `jieba`；未安装时自动退化为按字符切分，脚本仍可正常运行。
- 任务 2、3 会自动把图片保存到 `结果图/`，并在控制台输出准确率等评估结果。

## 五、说明
- 指导书示例代码里的 `get_feature_names()` 在 sklearn 1.2+ 已移除，本实验统一改用 `get_feature_names_out()`。
- 指导书示例里的 `load_boston` 已在 sklearn 1.2+ 移除（本实验未使用，改用乳腺癌 / 鸢尾花等内置数据集）。
