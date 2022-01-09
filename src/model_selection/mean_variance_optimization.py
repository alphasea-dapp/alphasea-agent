import cvxpy
import numpy as np
from sklearn.covariance import ledoit_wolf


def mean_variance_optimize(ret):
    mu = np.mean(ret, axis=0)
    S, _ = ledoit_wolf(ret)

    x = cvxpy.Variable(mu.shape[0])
    objective = cvxpy.Minimize(-mu @ x)

    constraints = [
        cvxpy.quad_form(x, S) <= 1,
        0 <= x,
    ]

    prob = cvxpy.Problem(objective, constraints)

    try:
        result = prob.solve()
        weight = x.value
        if weight is None:
            print('weight is None {} {}'.format(mu, S))
            weight = np.zeros(mu.size)
    except Exception as e:
        print(e)
        weight = np.zeros(mu.size)

    # 最適化が不完全な場合があるので
    weight[weight < 0] = 0

    return weight / (1e-37 + np.sum(np.abs(weight)))
