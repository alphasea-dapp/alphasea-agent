
class ModelSelectionParams:
    def __init__(self, df_ret, df_position, df_current, budget=None, random_state=None):
        self.df_ret = df_ret
        self.df_position = df_position
        self.df_current = df_current
        self.random_state = random_state
        self.budget = budget
        self.owner = None

        # df_ret: index: [execution_start_at], columns: model_id, values: ret
        # df_position: index: [execution_start_at], columns: model_id, values: position
        # df_current: index: [model_id], columns: [price]
        # df_ret.index == df_position.index
        # df_ret.columns == df_position.columns

    def validate(self):
        df_ret = self.df_ret
        df_position = self.df_position
        df_current = self.df_current

        assert(df_ret.index.equals(df_position.index))
        assert(df_ret.columns.equals(df_position.columns))
        assert(df_ret.columns.get_level_values('model_id').isin(df_current.index).all())

        assert(df_ret.index.name == 'execution_start_at')
        assert(df_position.index.name == 'execution_start_at')
        assert(df_current.index.name == 'model_id')
