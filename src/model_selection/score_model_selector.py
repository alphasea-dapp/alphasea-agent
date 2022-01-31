import numpy as np
import pandas as pd
from ..logger import create_null_logger
from .statistics import max_sprt_t_test_log_prob_ratio


def default_scorer(x):
    log_prob_ratio = max_sprt_t_test_log_prob_ratio(
        x[::-1],
        [0.01, 0.02, 0.04, 0.08, 0.16, 0.32]
    )
    return np.nanmax(log_prob_ratio)


class ScoreModelSelector:
    def __init__(self, execution_cost: float,
                 score_threshold=None,
                 scorer=None, logger=None):
        self._execution_cost = execution_cost
        self._scorer = default_scorer if scorer is None else scorer
        self._score_threshold = score_threshold
        self._logger = create_null_logger() if logger is None else logger

    def select_receivers(self, params):
        df_weight = self.select_model(params)
        return params.df_current.loc[df_weight.index, 'owner'].unique()

    def select_model(self, params):
        df_ret = params.df_ret
        df_position = params.df_position
        df_ret = df_ret * df_position

        # add execution cost
        df_ret -= df_position.diff(1).fillna(0).abs() * self._execution_cost

        # aggregate symbol
        df_ret = df_ret.groupby(level='model_id', axis=1).sum()

        df_current = params.df_current.copy()
        df_current['score'] = np.nan
        for model_id in df_ret.columns:
            score = self._scorer(df_ret[model_id].values)
            df_current.loc[model_id, 'score'] = score

            self._logger.debug('{} mean {} std {} sharpe {} score {}'.format(
                model_id,
                df_ret[model_id].mean(),
                df_ret[model_id].std(),
                df_ret[model_id].mean() / (1e-37 + df_ret[model_id].std()),
                score
            ))

        if params.owner is None:
            reference_score = df_current['score'].max()
        else:
            reference_score = df_current.loc[df_current['owner'] == params.owner, 'score'].max()

        df_current = df_current.loc[df_current['score'] >= reference_score - self._score_threshold]

        return pd.DataFrame(
            np.ones((df_current.shape[0], 1)) / (1e-37 + df_current.shape[0]),
            index=df_current.index, columns=['weight']
        )
