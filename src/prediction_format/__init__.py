from io import StringIO
import re
import numpy as np
import pandas as pd


class ValidationError(Exception):
    pass


def parse_content(content):
    csv_str = content.decode('utf-8')
    df = pd.read_csv(StringIO(csv_str), dtype=str)
    df['position'] = df['position'].astype(float)
    df = df.sort_values('symbol')
    df = df.set_index('symbol')

    return df


def normalize_content(content):
    csv_str = content.decode('utf-8')
    df = pd.read_csv(StringIO(csv_str), dtype=str)

    df = df.sort_values('symbol')
    df = pd.concat([df[['symbol']], df[['position']]], axis=1)

    output = StringIO()
    df.to_csv(output, index=False)

    return output.getvalue()[:-1].encode()  # remove last newline


def validate_content(content):
    try:
        csv_str = content.decode('utf-8')
    except Exception as e:
        raise ValidationError('decode failed') from e

    try:
        df = pd.read_csv(StringIO(csv_str), dtype=str)
    except Exception as e:
        raise ValidationError('read_csv failed') from e

    if df.shape[0] == 0:
        raise ValidationError('empty')

    if df.shape[1] != 2:
        raise ValidationError('column count must be 2')
    if 'position' not in df.columns:
        raise ValidationError('position column not found')
    if 'symbol' not in df.columns:
        raise ValidationError('symbol column not found')

    if df.isnull().any().any():
        raise ValidationError('contains NaN')

    for s in df['symbol']:
        validate_symbol(s)
    if df['symbol'].unique().size != df.shape[0]:
        raise ValidationError('duplicated symbol')

    try:
        float_position = df['position'].astype(float)
    except Exception as e:
        raise ValidationError('position contains non number') from e

    if float_position.isin([np.inf, -np.inf]).any():
        raise ValidationError('position contains inf')
    if float_position.abs().sum() > 1:
        raise ValidationError('sum of abs(position) must be in [-1, 1]')


def validate_symbol(s: str):
    if not re.match(r'^[a-zA-Z0-9]{1,8}$', s):
        raise ValidationError('invalid symbol')
