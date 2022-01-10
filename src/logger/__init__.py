from types import SimpleNamespace


def create_null_logger():
    return SimpleNamespace(
        debug=_null_logger_func,
        error=_null_logger_func,
        warn=_null_logger_func,
        info=_null_logger_func,
    )


def _null_logger_func(x):
    ...
