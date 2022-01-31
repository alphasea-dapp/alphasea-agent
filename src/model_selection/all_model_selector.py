import numpy as np
import pandas as pd


class AllModelSelector:

    def __init__(self):
        ...

    def select_receivers(self, params):
        return params.df_current['owner'].unique()

    def select_model(self, params):
        df_current = params.df_current
        model_count = df_current.shape[0]

        return pd.DataFrame(
            np.ones((model_count, 1)) / (1e-37 + model_count),
            index=df_current.index, columns=['weight']
        )
