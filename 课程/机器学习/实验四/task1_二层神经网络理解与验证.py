# -*- coding: utf-8 -*-
'''实验四任务1：理解感知机、二层神经网络和误差反向传播。'''
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from 神经网络.two_layer_net import TwoLayerNet


BASE = Path(__file__).resolve().parent
IMAGE_DIR = BASE / '结果图'
IMAGE_DIR.mkdir(exist_ok=True)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def perceptron(inputs, weights, bias):
    return int(np.dot(inputs, weights) + bias > 0)


def logic_gate_table():
    rows = []
    for x1, x2 in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        inputs = np.array([x1, x2])
        and_value = perceptron(inputs, np.array([0.5, 0.5]), -0.7)
        nand_value = perceptron(inputs, np.array([-0.5, -0.5]), 0.7)
        or_value = perceptron(inputs, np.array([0.5, 0.5]), -0.2)
        xor_value = perceptron(np.array([nand_value, or_value]), np.array([0.5, 0.5]), -0.7)
        rows.append([x1, x2, and_value, nand_value, or_value, xor_value])
    return rows


def gradient_check():
    network = TwoLayerNet(2, 4, 2, weight_init_std=0.1, rng=np.random.default_rng(7))
    inputs = np.array([[0.2, -0.4], [0.7, 0.1], [-0.3, 0.8]])
    targets = np.array([0, 1, 0])
    numerical = network.numerical_gradient(inputs, targets)
    backprop = network.gradient(inputs, targets)
    errors = {}
    for key in numerical:
        denominator = np.maximum(1.0, np.abs(numerical[key]) + np.abs(backprop[key]))
        errors[key] = float(np.max(np.abs(numerical[key] - backprop[key]) / denominator))
    return errors


def train_two_layer_network():
    inputs, targets = make_moons(n_samples=400, noise=0.2, random_state=42)
    train_x, test_x, train_y, test_y = train_test_split(
        inputs, targets, test_size=0.25, random_state=42, stratify=targets
    )
    scaler = StandardScaler()
    train_x = scaler.fit_transform(train_x)
    test_x = scaler.transform(test_x)
    network = TwoLayerNet(2, 12, 2, weight_init_std=0.25, rng=np.random.default_rng(42))
    random = np.random.default_rng(42)
    history = {'loss': [], 'train_accuracy': [], 'test_accuracy': []}
    for _ in range(180):
        order = random.permutation(len(train_x))
        for start in range(0, len(train_x), 32):
            indices = order[start:start + 32]
            gradients = network.gradient(train_x[indices], train_y[indices])
            for key in network.params:
                network.params[key] -= 0.08 * gradients[key]
        history['loss'].append(network.loss(train_x, train_y))
        history['train_accuracy'].append(network.accuracy(train_x, train_y))
        history['test_accuracy'].append(network.accuracy(test_x, test_y))
    return network, scaler, inputs, targets, history


def plot_logic_gates(rows):
    figure, axis = plt.subplots(figsize=(8, 3.5))
    axis.axis('off')
    table = axis.table(
        cellText=rows,
        colLabels=['x1', 'x2', 'AND', 'NAND', 'OR', 'XOR'],
        cellLoc='center',
        loc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.7)
    axis.set_title('单层感知机与多层组合实现逻辑门', pad=18)
    figure.tight_layout()
    figure.savefig(IMAGE_DIR / 'task1_感知机逻辑门.png', dpi=180, bbox_inches='tight')
    plt.close(figure)


def plot_gradient_errors(errors):
    figure, axis = plt.subplots(figsize=(7, 4.2))
    axis.bar(errors.keys(), errors.values(), color='#4c78a8')
    axis.set_yscale('log')
    axis.set_ylabel('最大相对误差（对数坐标）')
    axis.set_title('数值梯度与反向传播梯度检查')
    axis.grid(axis='y', alpha=0.25)
    figure.tight_layout()
    figure.savefig(IMAGE_DIR / 'task1_二层网络梯度检查.png', dpi=180)
    plt.close(figure)


def plot_training(network, scaler, inputs, targets, history):
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    epochs = np.arange(1, len(history['loss']) + 1)
    axes[0].plot(epochs, history['loss'], label='交叉熵损失', color='#e45756')
    axes[0].plot(epochs, history['train_accuracy'], label='训练准确率', color='#4c78a8')
    axes[0].plot(epochs, history['test_accuracy'], label='测试准确率', color='#59a14f')
    axes[0].set_xlabel('训练轮次')
    axes[0].set_title('二层神经网络训练过程')
    axes[0].legend()
    axes[0].grid(alpha=0.25)

    x_min, x_max = inputs[:, 0].min() - 0.5, inputs[:, 0].max() + 0.5
    y_min, y_max = inputs[:, 1].min() - 0.5, inputs[:, 1].max() + 0.5
    grid_x, grid_y = np.meshgrid(np.linspace(x_min, x_max, 260), np.linspace(y_min, y_max, 260))
    grid = np.c_[grid_x.ravel(), grid_y.ravel()]
    predictions = np.argmax(network.predict(scaler.transform(grid)), axis=1).reshape(grid_x.shape)
    axes[1].contourf(grid_x, grid_y, predictions, alpha=0.25, cmap='coolwarm')
    axes[1].scatter(inputs[:, 0], inputs[:, 1], c=targets, cmap='coolwarm', s=22, edgecolors='white')
    axes[1].set_title('二层神经网络分类边界（双月数据）')
    axes[1].set_xlabel('特征 1')
    axes[1].set_ylabel('特征 2')
    figure.tight_layout()
    figure.savefig(IMAGE_DIR / 'task1_二层网络训练与分类边界.png', dpi=180)
    plt.close(figure)


def main():
    rows = logic_gate_table()
    errors = gradient_check()
    network, scaler, inputs, targets, history = train_two_layer_network()
    plot_logic_gates(rows)
    plot_gradient_errors(errors)
    plot_training(network, scaler, inputs, targets, history)
    metrics = {
        'logic_gate_table': rows,
        'gradient_relative_errors': errors,
        'final_loss': history['loss'][-1],
        'final_train_accuracy': history['train_accuracy'][-1],
        'final_test_accuracy': history['test_accuracy'][-1],
    }
    (IMAGE_DIR / 'task1_metrics.json').write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print('逻辑门真值表：', rows)
    print('梯度检查最大相对误差：', errors)
    print('最终测试准确率：{:.4f}'.format(history['test_accuracy'][-1]))


if __name__ == '__main__':
    main()
