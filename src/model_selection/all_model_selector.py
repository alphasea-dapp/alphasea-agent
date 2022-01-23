import numpy as np
import pandas as pd


class AllModelSelector:

    def __init__(self):
        ...

    def select_model(self, df=None, df_market=None, df_model=None, random_state=None, budget=None):
        model_count = df_model.shape[0]

        return pd.DataFrame(
            np.ones((model_count, 1)) / (1e-37 + model_count),
            index=df_model.index, columns=['weight']
        )
