# -*- coding: utf-8 -*-
'''实验四任务2：由二层网络扩展为三层网络，并验证增加隐藏层后的训练过程。'''
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import make_circles
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from 神经网络.three_layer_net import ThreeLayerNet
from 神经网络.two_layer_net import TwoLayerNet


BASE = Path(__file__).resolve().parent
IMAGE_DIR = BASE / '结果图'
IMAGE_DIR.mkdir(exist_ok=True)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def train_network(network, train_x, train_y, test_x, test_y, epochs=260, learning_rate=0.08):
    random = np.random.default_rng(24)
    history = {'loss': [], 'train_accuracy': [], 'test_accuracy': []}
    for _ in range(epochs):
        order = random.permutation(len(train_x))
        for start in range(0, len(train_x), 48):
            indices = order[start:start + 48]
            gradients = network.gradient(train_x[indices], train_y[indices])
            for key in network.params:
                network.params[key] -= learning_rate * gradients[key]
        history['loss'].append(network.loss(train_x, train_y))
        history['train_accuracy'].append(network.accuracy(train_x, train_y))
        history['test_accuracy'].append(network.accuracy(test_x, test_y))
    return history


def three_layer_gradient_check():
    network = ThreeLayerNet(2, 3, 3, 2, weight_init_std=0.1, rng=np.random.default_rng(9))
    network.params['b1'][:] = 0.05
    network.params['b2'][:] = 0.05
    inputs = np.array([[0.2, -0.1], [-0.4, 0.7]])
    targets = np.array([1, 0])
    numerical = network.numerical_gradient(inputs, targets)
    backprop = network.gradient(inputs, targets)
    errors = {}
    for key in numerical:
        denominator = np.maximum(1.0, np.abs(numerical[key]) + np.abs(backprop[key]))
        errors[key] = float(np.max(np.abs(numerical[key] - backprop[key]) / denominator))
    return errors


def plot_comparison(two_history, three_history):
    epochs = np.arange(1, len(two_history['loss']) + 1)
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].plot(epochs, two_history['loss'], label='二层网络', color='#4c78a8')
    axes[0].plot(epochs, three_history['loss'], label='三层网络', color='#e45756')
    axes[0].set_title('训练损失对比')
    axes[0].set_xlabel('训练轮次')
    axes[0].set_ylabel('交叉熵损失')
    axes[0].legend()
    axes[0].grid(alpha=0.25)
    axes[1].plot(epochs, two_history['test_accuracy'], label='二层网络', color='#4c78a8')
    axes[1].plot(epochs, three_history['test_accuracy'], label='三层网络', color='#e45756')
    axes[1].set_title('测试准确率对比')
    axes[1].set_xlabel('训练轮次')
    axes[1].set_ylabel('准确率')
    axes[1].set_ylim(0.45, 1.02)
    axes[1].legend()
    axes[1].grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(IMAGE_DIR / 'task2_二层与三层网络训练对比.png', dpi=180)
    plt.close(figure)


def plot_boundaries(networks, scaler, inputs, targets):
    x_min, x_max = inputs[:, 0].min() - 0.25, inputs[:, 0].max() + 0.25
    y_min, y_max = inputs[:, 1].min() - 0.25, inputs[:, 1].max() + 0.25
    grid_x, grid_y = np.meshgrid(np.linspace(x_min, x_max, 280), np.linspace(y_min, y_max, 280))
    grid = np.c_[grid_x.ravel(), grid_y.ravel()]
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for axis, (title, network) in zip(axes, networks):
        predictions = np.argmax(network.predict(scaler.transform(grid)), axis=1).reshape(grid_x.shape)
        axis.contourf(grid_x, grid_y, predictions, alpha=0.25, cmap='coolwarm')
        axis.scatter(inputs[:, 0], inputs[:, 1], c=targets, cmap='coolwarm', s=18, edgecolors='white')
        axis.set_title(title)
        axis.set_xlabel('特征 1')
        axis.set_ylabel('特征 2')
    figure.tight_layout()
    figure.savefig(IMAGE_DIR / 'task2_二层与三层网络分类边界.png', dpi=180)
    plt.close(figure)


def plot_gradient_errors(errors):
    figure, axis = plt.subplots(figsize=(7.5, 4.3))
    axis.bar(errors.keys(), errors.values(), color='#59a14f')
    axis.set_yscale('log')
    axis.set_title('三层神经网络梯度检查')
    axis.set_ylabel('最大相对误差（对数坐标）')
    axis.grid(axis='y', alpha=0.25)
    figure.tight_layout()
    figure.savefig(IMAGE_DIR / 'task2_三层网络梯度检查.png', dpi=180)
    plt.close(figure)


def main():
    inputs, targets = make_circles(n_samples=600, noise=0.08, factor=0.38, random_state=24)
    train_x, test_x, train_y, test_y = train_test_split(
        inputs, targets, test_size=0.25, random_state=24, stratify=targets
    )
    scaler = StandardScaler()
    train_x = scaler.fit_transform(train_x)
    test_x = scaler.transform(test_x)
    two_layer = TwoLayerNet(2, 10, 2, weight_init_std=0.25, rng=np.random.default_rng(24))
    three_layer = ThreeLayerNet(2, 12, 8, 2, weight_init_std=0.25, rng=np.random.default_rng(24))
    two_history = train_network(two_layer, train_x, train_y, test_x, test_y)
    three_history = train_network(three_layer, train_x, train_y, test_x, test_y)
    errors = three_layer_gradient_check()
    plot_comparison(two_history, three_history)
    plot_boundaries(
        [('二层神经网络分类边界', two_layer), ('三层神经网络分类边界', three_layer)],
        scaler,
        inputs,
        targets,
    )
    plot_gradient_errors(errors)
    metrics = {
        'two_layer': {
            'final_loss': two_history['loss'][-1],
            'train_accuracy': two_history['train_accuracy'][-1],
            'test_accuracy': two_history['test_accuracy'][-1],
        },
        'three_layer': {
            'final_loss': three_history['loss'][-1],
            'train_accuracy': three_history['train_accuracy'][-1],
            'test_accuracy': three_history['test_accuracy'][-1],
        },
        'gradient_relative_errors': errors,
    }
    (IMAGE_DIR / 'task2_metrics.json').write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print('二层网络测试准确率：{:.4f}'.format(metrics['two_layer']['test_accuracy']))
    print('三层网络测试准确率：{:.4f}'.format(metrics['three_layer']['test_accuracy']))
    print('三层网络梯度检查：', errors)


if __name__ == '__main__':
    main()
