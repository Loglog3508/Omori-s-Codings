# -*- coding: utf-8 -*-
import numpy as np


def numerical_gradient(function, parameters, step=1e-4):
    gradient = np.zeros_like(parameters, dtype=float)
    iterator = np.nditer(parameters, flags=['multi_index'], op_flags=['readwrite'])
    while not iterator.finished:
        index = iterator.multi_index
        original = parameters[index]
        parameters[index] = original + step
        positive = function(parameters)
        parameters[index] = original - step
        negative = function(parameters)
        gradient[index] = (positive - negative) / (2 * step)
        parameters[index] = original
        iterator.iternext()
    return gradient
