import pandas as pd
from unittest import TestCase
from src.executor.utils import df_weight_to_purchase_params_list


class TestExecutorDfWeightToPurchaseParamsList(TestCase):
    def test_ok(self):
        df_weight = pd.DataFrame(
            [
                ['model1'],
                ['model2'],
                ['model_locally_stored'],
            ],
            columns=['model_id'],
        ).set_index(['model_id'])

        df_current = pd.DataFrame(
            [
                ['model1', None],
                ['model2', None],
                ['model_locally_stored', 'content'],
                ['model_df_current_only', None],
            ],
            columns=['model_id', 'content'],
        ).set_index(['model_id'])

        expected = [
            {
                'model_id': 'model1',
                'execution_start_at': 1
            },
            {
                'model_id': 'model2',
                'execution_start_at': 1
            }
        ]

        self.assertEqual(df_weight_to_purchase_params_list(
            df_current=df_current,
            df_weight=df_weight,
            execution_start_at=1,
        ), expected)
