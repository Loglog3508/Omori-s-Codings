# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

import numpy as np


BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from 神经网络.common.functions import cross_entropy_error, sigmoid, softmax
from 神经网络.common.layers import Affine, Relu, SoftmaxWithLoss
from 神经网络.three_layer_net import ThreeLayerNet
from 神经网络.two_layer_net import TwoLayerNet


class FunctionTests(unittest.TestCase):
    def test_sigmoid_is_stable_for_large_values(self):
        values = sigmoid(np.array([-1000.0, 0.0, 1000.0]))
        np.testing.assert_allclose(values, [0.0, 0.5, 1.0], atol=1e-12)
        self.assertTrue(np.isfinite(values).all())

    def test_softmax_normalizes_each_row(self):
        probabilities = softmax(np.array([[1001.0, 1002.0], [1.0, 1.0]]))
        np.testing.assert_allclose(probabilities.sum(axis=1), [1.0, 1.0])
        np.testing.assert_allclose(probabilities[0], [0.26894142, 0.73105858], rtol=1e-7)

    def test_cross_entropy_accepts_label_and_one_hot_targets(self):
        probabilities = np.array([[0.1, 0.7, 0.2], [0.8, 0.1, 0.1]])
        labels = np.array([1, 0])
        one_hot = np.eye(3)[labels]
        expected = (-np.log(0.7) - np.log(0.8)) / 2
        self.assertAlmostEqual(cross_entropy_error(probabilities, labels), expected, places=10)
        self.assertAlmostEqual(cross_entropy_error(probabilities, one_hot), expected, places=10)


class LayerTests(unittest.TestCase):
    def test_relu_backward_blocks_non_positive_inputs(self):
        layer = Relu()
        output = layer.forward(np.array([[-1.0, 0.0, 2.0]]))
        gradient = layer.backward(np.ones_like(output))
        np.testing.assert_array_equal(output, [[0.0, 0.0, 2.0]])
        np.testing.assert_array_equal(gradient, [[0.0, 0.0, 1.0]])

    def test_affine_backward_returns_parameter_gradients(self):
        weights = np.array([[1.0, 2.0], [3.0, 4.0]])
        bias = np.array([0.5, -0.5])
        layer = Affine(weights, bias)
        output = layer.forward(np.array([[1.0, 2.0]]))
        input_gradient = layer.backward(np.array([[2.0, -1.0]]))
        np.testing.assert_array_equal(output, [[7.5, 9.5]])
        np.testing.assert_array_equal(input_gradient, [[0.0, 2.0]])
        np.testing.assert_array_equal(layer.dW, [[2.0, -1.0], [4.0, -2.0]])
        np.testing.assert_array_equal(layer.db, [2.0, -1.0])

    def test_softmax_with_loss_gradient_matches_known_result(self):
        layer = SoftmaxWithLoss()
        loss = layer.forward(np.array([[2.0, 1.0, 0.0]]), np.array([0]))
        gradient = layer.backward()
        self.assertAlmostEqual(loss, 0.4076059644, places=9)
        np.testing.assert_allclose(
            gradient,
            [[-0.33475904, 0.24472847, 0.09003057]],
            rtol=1e-7,
        )


class NetworkTests(unittest.TestCase):
    def test_two_layer_backprop_matches_numerical_gradient(self):
        rng = np.random.default_rng(7)
        network = TwoLayerNet(2, 3, 2, weight_init_std=0.1, rng=rng)
        inputs = np.array([[0.2, -0.4], [0.7, 0.1]])
        targets = np.array([0, 1])
        numerical = network.numerical_gradient(inputs, targets)
        backprop = network.gradient(inputs, targets)
        for key in numerical:
            np.testing.assert_allclose(backprop[key], numerical[key], atol=1e-6, rtol=1e-4)

    def test_three_layer_network_learns_tiny_classification_problem(self):
        rng = np.random.default_rng(11)
        network = ThreeLayerNet(2, 8, 6, 2, weight_init_std=0.2, rng=rng)
        inputs = np.array([
            [-1.2, -0.9], [-0.8, -1.1], [-1.0, -0.6],
            [0.9, 1.2], [1.1, 0.8], [0.7, 1.0],
        ])
        targets = np.array([0, 0, 0, 1, 1, 1])
        initial_loss = network.loss(inputs, targets)
        for _ in range(300):
            gradients = network.gradient(inputs, targets)
            for key in network.params:
                network.params[key] -= 0.1 * gradients[key]
        self.assertLess(network.loss(inputs, targets), initial_loss * 0.1)
        self.assertEqual(network.accuracy(inputs, targets), 1.0)


if __name__ == '__main__':
    unittest.main()
