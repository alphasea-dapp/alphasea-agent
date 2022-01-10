
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from scipy.optimize import basinhopping
from .mean_variance_optimization import mean_variance_optimize

# 未完成
# class MeanVarianceModelSelector:
#
#     def __init__(self, execution_cost: float,
#                  assets: float, budget: float, max_allowed_correlation: float,
#                  symbol_white_list: list):
#         ...
#
#     def select_model(self, df=None, df_model=None, random_state=None):
#         # symbolホワイトリスト
#         df = df.loc[df.index.get_level_values('symbol').isin(self._symbol_white_list)]
#
#         # 取引コストを反映
#         position_diff = df['position'] - df.groupby(['model_id', 'symbol'])['position'].shift(1)
#         df['ret'] -= position_diff.abs() * self._execution_cost
#
#         # symbol集約
#         df = pd.concat([
#             df.groupby(['model_id', 'execution_start_at'])['ret'].sum()
#         ], axis=1)
#         df_ret = df.pivot(index='execution_start_at', columns='model_id', values='ret')
#
#         # 最適化
#         ret_numpy = df_ret.values
#         df_model = df_model.loc[df_ret.columns]
#         price_numpy = df_model['price'].values
#
#         model_count = df_ret.shape[1]
#         rs = np.random.RandomState(random_state)
#
#         def func(x):
#             if np.sum(x) == 0:
#                 return 0
#
#             ret_selected = ret_numpy[:, x]
#             weight = mean_variance_optimize(ret_selected)
#
#             ret_agg = np.sum(ret_selected * weight, axis=1)
#             ret_mean = np.mean(ret_agg)
#             ret_std = np.std(ret_agg)
#             cost = np.sum(price_numpy[x]) / self._assets
#
#             sharpe = (ret_mean - cost) / (1e-37 + ret_std)
#
#             return -sharpe
#
#         def take_step(x):
#             sum_x = np.sum(x)
#             if rs.randint(2) == 0:
#                 if sum_x == 0:
#                     return x
#                 else:
#                     x = x.copy()
#                     x[rs.choice(x, p=x / sum_x)] = 0
#                     return x
#             else:
#                 if sum_x == x.size:
#                     return x
#                 else:
#                     x = x.copy()
#                     x[rs.choice(x, p=(1 - x) / (x.size - sum_x))] = 1
#                     return x
#
#         x = basinhopping(
#             func,
#             np.zeros(model_count),
#             niter=100,
#             T=1.0,
#             take_step=take_step,
#             disp=True,
#         )
#
#         ret_selected = ret_numpy[:, x]
#         weight, score = mean_variance_optimize(ret_selected)
#
#         return pd.DataFrame([
#             weight
#         ], columns=df_ret.columns)
