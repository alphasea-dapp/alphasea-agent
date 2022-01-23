import traceback
import pandas as pd
from ..prediction_format import validate_content, parse_content

day_seconds = 24 * 60 * 60


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
        if df_current.loc[model_id, 'locally_stored']:
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
        columns=['model_id', 'price', 'locally_stored', 'content']
    ).set_index('model_id')
    df_current = df_current.sort_index()
    # メモリにあるモデルの購入費用は0
    df_current.loc[df_current['locally_stored'], 'price'] = 0
    return df_current


def fetch_historical_predictions(
        store, tournament_id,
        execution_start_at, evaluation_periods,
        logger):
    without_fetch_events = False

    dfs = []
    for i in range(2, 2 + evaluation_periods):
        predictions = store.fetch_predictions(
            tournament_id=tournament_id,
            execution_start_at=execution_start_at - day_seconds * i,
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
