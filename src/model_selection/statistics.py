import numpy as np
from scipy.special import gamma, hyp1f1, loggamma


# without nc independent factor
# https://en.wikipedia.org/wiki/Noncentral_t-distribution
def nct_log_pdf(t, df, nc):
    t2 = t ** 2

    c1 = nc ** 2 * t2 / (2 * (t2 + df))
    c2 = 2.0 ** 0.5 * nc * t / (t2 + df) ** 0.5 * np.exp(loggamma(df / 2.0 + 1) - loggamma((df + 1.0) / 2))
    a = hyp1f1((df + 1.0) / 2, 0.5, c1)
    b = hyp1f1(df / 2.0 + 1, 1.5, c1) * c2

    return -nc ** 2 / 2 + np.log(a + b)


def cum_t_value(x):
    n = np.arange(2, 1 + x.shape[0])
    mean = np.cumsum(x)[1:] / n
    var = np.cumsum(x ** 2)[1:] - n * mean ** 2
    var = np.maximum(0.0, var) / (n - 1)
    t = np.empty(x.shape[0])
    t[0] = np.nan
    t[1:] = mean / (var / n) ** 0.5
    return t


def sprt_t_test_log_prob_ratio(x, effect_size):
    t_value = cum_t_value(x)
    df = np.arange(x.shape[0])
    nc = effect_size * np.arange(1, 1 + x.shape[0]) ** 0.5
    log_p0 = nct_log_pdf(t_value, df, 0.0)
    log_p1 = nct_log_pdf(t_value, df, nc)
    log_ratio = log_p1 - log_p0
    return log_ratio


def max_sprt_t_test_log_prob_ratio(x, effect_sizes):
    log_ratio = sprt_t_test_log_prob_ratio(x, effect_sizes[0])
    for effect_size in effect_sizes[1:]:
        log_ratio = np.maximum(log_ratio, sprt_t_test_log_prob_ratio(x, effect_size))
    return log_ratio
