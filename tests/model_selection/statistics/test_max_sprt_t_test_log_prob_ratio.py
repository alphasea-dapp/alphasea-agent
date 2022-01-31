from unittest import TestCase
import numpy as np
from src.model_selection.statistics import max_sprt_t_test_log_prob_ratio


class TestMaxSprtTTestLogProbRatio(TestCase):
    def test_smoke(self):
        x = np.array([-1, 0, 1, 2])

        log_prob_ratio = max_sprt_t_test_log_prob_ratio(x, [0.1, 0.2])
        self.assertEqual(log_prob_ratio.shape, (4, ))
        self.assertTrue(np.isnan(log_prob_ratio[0]))
        self.assertFalse(np.isnan(log_prob_ratio[1]))
        self.assertFalse(np.isnan(log_prob_ratio[2]))
        self.assertFalse(np.isnan(log_prob_ratio[3]))
