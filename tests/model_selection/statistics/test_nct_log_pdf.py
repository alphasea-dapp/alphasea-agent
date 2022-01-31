from unittest import TestCase
import numpy as np
from scipy.stats import nct
from numpy.testing import assert_array_almost_equal_nulp
from src.model_selection.statistics import nct_log_pdf


class TestNctLogPdf(TestCase):
    def test_ok(self):
        t = np.array([-1, 0, 1, 2])
        df = np.array([1, 2, 3, 4])
        log_prob_ratio = nct_log_pdf(t, df, 2) - nct_log_pdf(t, df, 1)

        reference = nct.logpdf(t, df, 2) - nct.logpdf(t, df, 1)
        assert_array_almost_equal_nulp(log_prob_ratio, reference, 32)
