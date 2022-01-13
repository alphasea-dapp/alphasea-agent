import logging
from logging import getLogger, StreamHandler
from types import SimpleNamespace


def create_logger(log_level):
    level = getattr(logging, log_level.upper())
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger = getLogger('alphasea-agent')
    logger.setLevel(level)
    logger.propagate = False

    err = StreamHandler()
    err.setLevel(level)
    err.setFormatter(formatter)
    logger.addHandler(err)

    return logger


def set_log_level_web3(log_level):
    level = getattr(logging, log_level.upper())
    logging.getLogger('web3.RequestManager').setLevel(level)
    logging.getLogger('web3.providers.HTTPProvider').setLevel(level)


def create_null_logger():
    return SimpleNamespace(
        debug=_null_logger_func,
        error=_null_logger_func,
        warn=_null_logger_func,
        info=_null_logger_func,
    )


def _null_logger_func(x):
    ...
