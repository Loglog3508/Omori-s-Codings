# -*- coding: utf-8 -*-
'''实验四任务3：使用纯 NumPy 三层神经网络完成手写数字分类。'''
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import load_digits
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from 神经网络.three_layer_net import ThreeLayerNet


BASE = Path(__file__).resolve().parent
IMAGE_DIR = BASE / '结果图'
MODEL_DIR = BASE / '模型'
IMAGE_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def train_digits_network(train_x, train_y, test_x, test_y):
    random = np.random.default_rng(42)
    network = ThreeLayerNet(64, 64, 32, 10, weight_init_std=0.12, rng=random)
    history = {'loss': [], 'train_accuracy': [], 'test_accuracy': []}
    for _ in range(50):
        order = random.permutation(len(train_x))
        for start in range(0, len(train_x), 64):
            indices = order[start:start + 64]
            gradients = network.gradient(train_x[indices], train_y[indices])
            for key in network.params:
                network.params[key] -= 0.05 * gradients[key]
        history['loss'].append(network.loss(train_x, train_y))
        history['train_accuracy'].append(network.accuracy(train_x, train_y))
        history['test_accuracy'].append(network.accuracy(test_x, test_y))
    return network, history


def plot_training_history(history):
    epochs = np.arange(1, len(history['loss']) + 1)
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].plot(epochs, history['loss'], color='#e45756')
    axes[0].set_title('手写数字分类训练损失')
    axes[0].set_xlabel('训练轮次')
    axes[0].set_ylabel('交叉熵损失')
    axes[0].grid(alpha=0.25)
    axes[1].plot(epochs, history['train_accuracy'], label='训练集', color='#4c78a8')
    axes[1].plot(epochs, history['test_accuracy'], label='测试集', color='#59a14f')
    axes[1].set_title('训练集与测试集准确率')
    axes[1].set_xlabel('训练轮次')
    axes[1].set_ylabel('准确率')
    axes[1].set_ylim(0.3, 1.01)
    axes[1].legend()
    axes[1].grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(IMAGE_DIR / 'task3_手写数字_损失与准确率.png', dpi=180)
    plt.close(figure)


def plot_confusion_matrix(test_y, predictions):
    figure, axis = plt.subplots(figsize=(7.2, 6.5))
    ConfusionMatrixDisplay.from_predictions(
        test_y,
        predictions,
        labels=np.arange(10),
        cmap='Blues',
        colorbar=False,
        ax=axis,
    )
    axis.set_title('手写数字测试集混淆矩阵')
    figure.tight_layout()
    figure.savefig(IMAGE_DIR / 'task3_手写数字_混淆矩阵.png', dpi=180)
    plt.close(figure)


def plot_sample_predictions(images, labels, predictions):
    random = np.random.default_rng(6)
    correct = np.where(labels == predictions)[0]
    incorrect = np.where(labels != predictions)[0]
    chosen = list(random.choice(correct, size=12, replace=False))
    if len(incorrect) >= 8:
        chosen.extend(random.choice(incorrect, size=8, replace=False))
    else:
        chosen.extend(incorrect.tolist())
    figure, axes = plt.subplots(4, 5, figsize=(10, 8))
    for axis, index in zip(axes.ravel(), chosen):
        axis.imshow(images[index], cmap='gray_r')
        color = '#2a9d8f' if labels[index] == predictions[index] else '#d62828'
        axis.set_title('真值 {} / 预测 {}'.format(labels[index], predictions[index]), color=color, fontsize=9)
        axis.axis('off')
    for axis in axes.ravel()[len(chosen):]:
        axis.axis('off')
    figure.suptitle('手写数字分类样例（红色为错误预测）')
    figure.tight_layout()
    figure.savefig(IMAGE_DIR / 'task3_手写数字_预测样例.png', dpi=180)
    plt.close(figure)


def plot_per_class_f1(report):
    scores = [report[str(number)]['f1-score'] for number in range(10)]
    figure, axis = plt.subplots(figsize=(8.5, 4.3))
    bars = axis.bar(np.arange(10), scores, color='#4c78a8')
    axis.set_xticks(np.arange(10))
    axis.set_xlabel('数字类别')
    axis.set_ylabel('F1 分数')
    axis.set_ylim(0.75, 1.01)
    axis.set_title('各数字类别 F1 分数')
    axis.bar_label(bars, fmt='%.2f', fontsize=8)
    axis.grid(axis='y', alpha=0.25)
    figure.tight_layout()
    figure.savefig(IMAGE_DIR / 'task3_手写数字_各类别F1.png', dpi=180)
    plt.close(figure)


def save_model(network, scaler):
    np.savez(
        MODEL_DIR / 'digits_three_layer_network.npz',
        **network.params,
        scaler_mean=scaler.mean_,
        scaler_scale=scaler.scale_,
    )


def main():
    digits = load_digits()
    train_x, test_x, train_y, test_y, _, test_images = train_test_split(
        digits.data,
        digits.target,
        digits.images,
        test_size=0.2,
        random_state=42,
        stratify=digits.target,
    )
    scaler = StandardScaler()
    train_x = scaler.fit_transform(train_x)
    test_x = scaler.transform(test_x)
    network, history = train_digits_network(train_x, train_y, test_x, test_y)
    predictions = np.argmax(network.predict(test_x), axis=1)
    report = classification_report(test_y, predictions, output_dict=True, zero_division=0)
    metrics = {
        'dataset_samples': int(len(digits.data)),
        'train_samples': int(len(train_x)),
        'test_samples': int(len(test_x)),
        'accuracy': float(accuracy_score(test_y, predictions)),
        'macro_f1': float(f1_score(test_y, predictions, average='macro')),
        'final_loss': history['loss'][-1],
        'classification_report': report,
    }
    plot_training_history(history)
    plot_confusion_matrix(test_y, predictions)
    plot_sample_predictions(test_images, test_y, predictions)
    plot_per_class_f1(report)
    save_model(network, scaler)
    (IMAGE_DIR / 'task3_metrics.json').write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print('数据集规模：{}，训练集：{}，测试集：{}'.format(len(digits.data), len(train_x), len(test_x)))
    print('测试准确率：{:.4f}'.format(metrics['accuracy']))
    print('宏平均 F1：{:.4f}'.format(metrics['macro_f1']))


if __name__ == '__main__':
    main()
