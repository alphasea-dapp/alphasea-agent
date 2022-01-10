import numpy as np
from scipy.stats import pearsonr

# def drop_high_correlation_columns(df_ret, max_allowed_correlation=None):
#     removed_symbols = []
#     for i in range(df_ret.shape[1]):
#         for j in range(i + 1, df_ret.shape[1]):
#             r, p = pearsonr(df_ret.iloc[i], df_ret.iloc[j])
#             if np.abs(r) > max_allowed_correlation:
#                 if df_ret.iloc[i].mean() < df_ret.iloc[j].mean():
#                     removed_symbols.append(df_ret.columns[i])
#                 else:
#                     removed_symbols.append(df_ret.columns[j])
#     df_ret = df_ret.drop(columns=removed_symbols)
#     return df_ret
