# -*- coding: utf-8 -*-
import numpy as np

from .functions import cross_entropy_error, softmax


class Relu:
    def __init__(self):
        self.mask = None

    def forward(self, inputs):
        self.mask = inputs <= 0
        outputs = inputs.copy()
        outputs[self.mask] = 0
        return outputs

    def backward(self, upstream_gradient):
        gradient = upstream_gradient.copy()
        gradient[self.mask] = 0
        return gradient


class Affine:
    def __init__(self, weights, bias):
        self.W = weights
        self.b = bias
        self.x = None
        self.dW = None
        self.db = None

    def forward(self, inputs):
        self.x = inputs
        return np.dot(inputs, self.W) + self.b

    def backward(self, upstream_gradient):
        input_gradient = np.dot(upstream_gradient, self.W.T)
        self.dW = np.dot(self.x.T, upstream_gradient)
        self.db = np.sum(upstream_gradient, axis=0)
        return input_gradient


class SoftmaxWithLoss:
    def __init__(self):
        self.loss = None
        self.y = None
        self.t = None

    def forward(self, inputs, targets):
        self.t = np.asarray(targets)
        self.y = softmax(inputs)
        self.loss = cross_entropy_error(self.y, self.t)
        return self.loss

    def backward(self, upstream_gradient=1):
        batch_size = self.y.shape[0]
        if self.t.ndim == 2:
            gradient = (self.y - self.t) / batch_size
        else:
            gradient = self.y.copy()
            gradient[np.arange(batch_size), self.t.astype(int)] -= 1
            gradient /= batch_size
        return gradient * upstream_gradient
