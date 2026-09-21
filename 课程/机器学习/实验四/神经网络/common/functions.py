# -*- coding: utf-8 -*-
import numpy as np


def sigmoid(x):
    values = np.asarray(x, dtype=float)
    result = np.empty_like(values)
    positive = values >= 0
    result[positive] = 1.0 / (1.0 + np.exp(-values[positive]))
    exp_values = np.exp(values[~positive])
    result[~positive] = exp_values / (1.0 + exp_values)
    return result


def softmax(x):
    values = np.asarray(x, dtype=float)
    if values.ndim == 1:
        shifted = values - np.max(values)
        exponentials = np.exp(shifted)
        return exponentials / np.sum(exponentials)
    shifted = values - np.max(values, axis=1, keepdims=True)
    exponentials = np.exp(shifted)
    return exponentials / np.sum(exponentials, axis=1, keepdims=True)


def cross_entropy_error(probabilities, targets):
    probabilities = np.asarray(probabilities, dtype=float)
    targets = np.asarray(targets)
    if probabilities.ndim == 1:
        probabilities = probabilities.reshape(1, -1)
    if targets.ndim == 0:
        targets = targets.reshape(1)
    if targets.ndim == 2:
        targets = np.argmax(targets, axis=1)
    batch_indices = np.arange(probabilities.shape[0])
    selected = probabilities[batch_indices, targets.astype(int)]
    return float(-np.mean(np.log(selected + 1e-12)))
