import traceback
import pandas as pd
from ..prediction_format import validate_content, parse_content
from ..model_selection.model_selection_params import ModelSelectionParams

day_seconds = 24 * 60 * 60


def create_model_selection_params(
        df, df_current, df_market, execution_start_ats, symbols):
    df = df.join(df_market, on=['execution_start_at', 'symbol'], how='left')

    df = df.loc[df.index.get_level_values('model_id').isin(df_current.index)]
    df = df.loc[df.index.get_level_values('symbol').isin(symbols)]

    params = ModelSelectionParams(
        df_ret=_pivot_df(df, execution_start_ats, 'ret'),
        df_position=_pivot_df(df, execution_start_ats, 'position'),
        df_current=df_current.copy(),
    )
    params.validate()
    return params


def _pivot_df(df, execution_start_ats, values):
    df = df.reset_index().pivot(
        index='execution_start_at',
        columns=['model_id', 'symbol'],
        values=values
    )
    df = df.fillna(0)
    df = df.reindex(execution_start_ats, fill_value=0)
    df = df.sort_index(axis=1)
    return df


# df_blended_listの順番は過去から最近
def calc_target_positions(t, df_blended_list):
    df_target = pd.concat(df_blended_list[1:]).groupby('symbol').sum() / (len(df_blended_list) - 1)
    df_target_prev = pd.concat(df_blended_list[:-1]).groupby('symbol').sum() / (len(df_blended_list) - 1)

    df_target['position'] *= t
    df_target_prev['position'] *= 1 - t

    df = pd.concat([df_target, df_target_prev]).groupby('symbol').sum()
    df = df.sort_index()
    return df


def floor_to_execution_start_at(timestamp, tournament):
    execution_lag = (
            tournament['prediction_time']
            + tournament['purchase_time']
            + tournament['shipping_time']
            + tournament['execution_preparation_time']
    )
    execution_start_at = (
            ((timestamp - execution_lag) // tournament['execution_time'])
            * tournament['execution_time']
            + execution_lag
    )
    t = 1.0 * (timestamp - execution_start_at) / tournament['execution_time']
    return execution_start_at, t


def blend_predictions(df_weight, df_current, logger=None):
    empty_result = pd.DataFrame([], columns=['symbol', 'position']).set_index('symbol')

    if df_weight is None:
        return empty_result

    dfs = []
    for model_id in df_weight.index:
        try:
            pred = df_current.loc[model_id]
            validate_content(pred['content'])
            df = parse_content(pred['content'])
            df['position'] *= df_weight.loc[model_id, 'weight']
            df = df.reset_index()
            dfs.append(df)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    if len(dfs) == 0:
        return empty_result

    df = pd.concat(dfs)

    return pd.concat([
        df.groupby('symbol')['position'].sum()
    ], axis=1)


def df_weight_to_purchase_params_list(
        df_current, df_weight, execution_start_at):
    create_purchase_params_list = []
    for model_id in df_weight.index:
        if not pd.isna(df_current.loc[model_id, 'content']):
            continue
        create_purchase_params_list.append({
            'model_id': model_id,
            'execution_start_at': execution_start_at
        })
    return create_purchase_params_list


def fetch_current_predictions(store, tournament_id, execution_start_at):
    current_predictions = store.fetch_predictions(
        tournament_id=tournament_id,
        execution_start_at=execution_start_at
    )
    df_current = pd.DataFrame(
        current_predictions,
        columns=['model_id', 'price', 'content']
    ).set_index('model_id')
    df_current = df_current.sort_index()
    # すでにcontentにアクセスできる場合は購入費用ゼロ
    df_current.loc[~pd.isna(df_current['content']), 'price'] = 0
    return df_current


def fetch_historical_predictions(
        store, tournament_id,
        execution_start_ats,
        logger):
    without_fetch_events = False

    dfs = []
    for execution_start_at in execution_start_ats:
        predictions = store.fetch_predictions(
            tournament_id=tournament_id,
            execution_start_at=execution_start_at,
            without_fetch_events=without_fetch_events,
        )
        without_fetch_events = True

        for prediction in predictions:
            try:
                dfs.append(_prediction_to_df(prediction))
            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())

    if len(dfs) == 0:
        df = pd.DataFrame(
            [],
            columns=['model_id', 'execution_start_at', 'symbol', 'position']
        ).set_index(['model_id', 'execution_start_at', 'symbol'])
    else:
        df = pd.concat(dfs)
    return df.sort_index()


def _prediction_to_df(prediction):
    validate_content(prediction['content'])
    df = parse_content(prediction['content'])
    df['model_id'] = prediction['model_id']
    df['execution_start_at'] = prediction['execution_start_at']
    df = df.reset_index().set_index(['model_id', 'execution_start_at', 'symbol'])
    return df
