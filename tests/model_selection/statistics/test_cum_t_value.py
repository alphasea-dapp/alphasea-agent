from unittest import TestCase
import numpy as np
from scipy.stats import ttest_1samp
from numpy.testing import assert_array_equal
from src.model_selection.statistics import cum_t_value


class TestCumTValue(TestCase):
    def test_ok(self):
        x = np.array([-1, 0, 1, 2])
        t_value = cum_t_value(x)

        reference = []
        for i in range(x.shape[0]):
            reference.append(ttest_1samp(x[:i + 1], 0)[0])
        reference = np.array(reference)

        assert_array_equal(t_value, reference)
