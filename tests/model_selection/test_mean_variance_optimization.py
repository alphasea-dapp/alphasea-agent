from unittest import TestCase
import numpy as np
from numpy.testing import assert_array_equal
from src.model_selection.mean_variance_optimization import mean_variance_optimize


class TestMeanVarianceOptimization(TestCase):
    def test_ok(self):
        weight = mean_variance_optimize(np.array([
            [1],
            [2],
            [3],
        ]))

        assert_array_equal(weight, [1])

    def test_weight_normalize(self):
        weight = mean_variance_optimize(np.array([
            [0.01, 0.03],
            [0.02, 0.02],
            [0.03, 0.01],
        ]))

        assert_array_equal(weight, [0.5, 0.5])

    def test_nonnegative_constraint(self):
        weight = mean_variance_optimize(np.array([
            [-1]
        ]))

        assert_array_equal(weight, [0])

    def test_error(self):
        weight = mean_variance_optimize(np.array([
            [np.nan]
        ]))

        assert_array_equal(weight, [0])

    def test_error2(self):
        weight = mean_variance_optimize(np.array([
            [1]
        ]))

        assert_array_equal(weight, [0])
