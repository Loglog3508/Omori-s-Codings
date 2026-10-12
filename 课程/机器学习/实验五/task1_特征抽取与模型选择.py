# -*- coding: utf-8 -*-
"""
实验五 任务1：理解 sklearn 的模型选择与特征抽取方法

对应指导书：理解下面代码中的文本相关模型选择和特征抽取的方法。
本脚本复现并逐段演示 DictVectorizer、CountVectorizer、TfidfVectorizer 以及
train_test_split 的用法，中文分词优先使用 jieba，未安装时退化为按字符切分。
"""
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

# 中文分词：优先 jieba，未安装时退化为按字符切分（结果仍可演示向量化过程）
try:
    import jieba

    def cut_word(text):
        return " ".join(jieba.cut(text))
except ImportError:
    def cut_word(text):
        return " ".join(ch for ch in text if ch.strip())


def count_demo():
    print("=" * 70)
    print("1. CountVectorizer：英文词频向量化")
    print("=" * 70)
    datas = ["i like playing football",
             "you like playing basketball",
             "he likes music"]
    transfer = CountVectorizer()
    data_new = transfer.fit_transform(datas)
    print("词表(特征名)：", transfer.get_feature_names_out())
    print("词频矩阵(稀疏表示)：")
    print(data_new)
    print("词频矩阵(稠密数组)：")
    print(data_new.toarray())


def text_demo():
    print("=" * 70)
    print("2. DictVectorizer：字典特征抽取（类别特征 one-hot 化）")
    print("=" * 70)
    datas = [{"course": "python程序设计", "hours": 40},
             {"course": "java", "hours": 56},
             {"course": "机器学习", "hours": 64},
             {"course": "python程序设计", "hours": 640}]
    transfer = DictVectorizer(sparse=False)
    data_new = transfer.fit_transform(datas)
    print("特征名：", transfer.get_feature_names_out())
    print(data_new)


def dataset_demo():
    print("=" * 70)
    print("3. 数据集划分：load_iris + train_test_split")
    print("=" * 70)
    iris = load_iris()
    x_train, x_test, y_train, y_test = train_test_split(
        iris.data, iris.target, test_size=0.2, random_state=20)
    print("训练集形状：", x_train.shape, "  测试集形状：", x_test.shape)
    print("y_train：", y_train)
    print("y_test ：", y_test)


def count_demo2():
    print("=" * 70)
    print("4. 中文文本 + CountVectorizer（jieba 分词 / 字符回退）")
    print("=" * 70)
    datas = ["身处大别山腹地的大湾村曾经和安徽其他的贫困村一样，交通不便，发展滞后，贫困发生率居高不下。"]
    data_new = []
    for sent in datas:
        data_new.append(cut_word(sent))
    print("分词结果(前 60 字符)：", data_new[0][:60], "...")
    transfer = CountVectorizer(stop_words=["的"], tokenizer=str.split, token_pattern=None)
    data_new = transfer.fit_transform(data_new)
    print("特征名：", transfer.get_feature_names_out())
    print("词频矩阵：", data_new.toarray())


def count_demo3():
    print("=" * 70)
    print("5. 中文文本 + TfidfVectorizer（TF-IDF 权重）")
    print("=" * 70)
    datas = ["贫困村小康社会全部出列，全面建成小康社会目标如期实现。"]
    data_new = []
    for sent in datas:
        data_new.append(cut_word(sent))
    transfer = TfidfVectorizer(stop_words=["的"], tokenizer=str.split, token_pattern=None)
    data_new = transfer.fit_transform(data_new)
    print("特征名：", transfer.get_feature_names_out())
    print("TF-IDF 矩阵：")
    print(data_new.toarray())


if __name__ == "__main__":
    count_demo()
    text_demo()
    dataset_demo()
    count_demo2()
    count_demo3()
