import numpy as np
import pandas as pd
from simanneal import Annealer


class EqualWeightModelSelector:

    def __init__(self, execution_cost: float,
                 assets: float):
        self._execution_cost = execution_cost
        self._assets = assets

    def select_model(self, params):
        df_ret = params.df_ret
        df_position = params.df_position
        df_ret = df_ret * df_position

        # add execution cost
        df_ret -= df_position.diff(1).fillna(0).abs() * self._execution_cost

        # aggregate symbol
        df_ret = df_ret.groupby(level='model_id', axis=1).sum()

        # 最適化
        problem = Problem(
            np.zeros(df_ret.shape[1], dtype=np.bool),
            ret_numpy=df_ret.values,
            price_numpy=params.df_current.loc[df_ret.columns, 'price'].values,
            assets=self._assets,
            budget=int(params.budget),
            random_state=params.random_state,
        )
        # TODO: anneal depends random.random
        x, energy = problem.anneal()

        if energy > 0:
            x = np.zeros(df_ret.shape[1], dtype=np.bool)

        return pd.DataFrame(
            np.ones((np.sum(x), 1)) / (1e-37 + np.sum(x)),
            index=df_ret.columns[x], columns=['weight']
        )


class Problem(Annealer):
    def __init__(self, state, ret_numpy=None, price_numpy=None, assets=None, budget=None, random_state=None):
        super().__init__(state, disable_signal=True)

        self._ret_numpy = ret_numpy
        self._price_numpy = price_numpy
        self._assets = assets
        self._budget = budget
        self._rs = np.random.RandomState(random_state)

    def move(self):
        x = self.state
        rs = self._rs

        sum_x = np.sum(x * 1.0)
        if rs.randint(2) == 0:
            if sum_x > 0:
                self.state[rs.choice(np.arange(x.size), p=x * 1.0 / sum_x)] = False
        else:
            if sum_x < x.size:
                self.state[rs.choice(np.arange(x.size), p=(1 - x * 1.0) / (x.size - sum_x))] = True

    def energy(self):
        x = self.state
        if np.sum(x) == 0:
            return 0

        ret_selected = self._ret_numpy[:, x]

        ret_agg = np.mean(ret_selected, axis=1)
        ret_mean = np.mean(ret_agg)
        ret_std = np.std(ret_agg)
        cost = np.sum(self._price_numpy[x])

        sharpe = (ret_mean - cost / self._assets) / (1e-37 + ret_std)

        if cost > self._budget:
            return 1000 - sharpe
        else:
            return -sharpe
