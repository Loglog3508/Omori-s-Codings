# -*- coding: utf-8 -*-
from collections import OrderedDict

import numpy as np

from .common.gradient import numerical_gradient
from .common.layers import Affine, Relu, SoftmaxWithLoss


class ThreeLayerNet:
    def __init__(
        self,
        input_size,
        hidden_size1,
        hidden_size2,
        output_size,
        weight_init_std=0.01,
        rng=None,
    ):
        random = rng if rng is not None else np.random.default_rng()
        self.params = {
            'W1': weight_init_std * random.standard_normal((input_size, hidden_size1)),
            'b1': np.zeros(hidden_size1),
            'W2': weight_init_std * random.standard_normal((hidden_size1, hidden_size2)),
            'b2': np.zeros(hidden_size2),
            'W3': weight_init_std * random.standard_normal((hidden_size2, output_size)),
            'b3': np.zeros(output_size),
        }
        self.layers = OrderedDict([
            ('Affine1', Affine(self.params['W1'], self.params['b1'])),
            ('Relu1', Relu()),
            ('Affine2', Affine(self.params['W2'], self.params['b2'])),
            ('Relu2', Relu()),
            ('Affine3', Affine(self.params['W3'], self.params['b3'])),
        ])
        self.last_layer = SoftmaxWithLoss()

    def predict(self, inputs):
        outputs = inputs
        for layer in self.layers.values():
            outputs = layer.forward(outputs)
        return outputs

    def loss(self, inputs, targets):
        return self.last_layer.forward(self.predict(inputs), targets)

    def accuracy(self, inputs, targets):
        predictions = np.argmax(self.predict(inputs), axis=1)
        labels = np.argmax(targets, axis=1) if np.asarray(targets).ndim == 2 else targets
        return float(np.mean(predictions == labels))

    def numerical_gradient(self, inputs, targets):
        loss_function = lambda _: self.loss(inputs, targets)
        return {
            key: numerical_gradient(loss_function, value)
            for key, value in self.params.items()
        }

    def gradient(self, inputs, targets):
        self.loss(inputs, targets)
        upstream_gradient = self.last_layer.backward()
        for layer in reversed(list(self.layers.values())):
            upstream_gradient = layer.backward(upstream_gradient)
        return {
            'W1': self.layers['Affine1'].dW,
            'b1': self.layers['Affine1'].db,
            'W2': self.layers['Affine2'].dW,
            'b2': self.layers['Affine2'].db,
            'W3': self.layers['Affine3'].dW,
            'b3': self.layers['Affine3'].db,
        }
