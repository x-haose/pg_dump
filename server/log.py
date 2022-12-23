import logging
import logging.config
import sys

from loguru import logger as _logger

# noinspection PyProtectedMember
from loguru._defaults import env


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists.
        try:
            level = _logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        # noinspection PyProtectedMember,PyUnresolvedReferences
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        fmt = "%(message)s"
        sanic_access_fmt = "[%(host)s]: %(request)s %(message)s %(status)d %(byte)s"
        fmt = fmt if record.name != "sanic.access" else sanic_access_fmt
        formatter = logging.Formatter(fmt=fmt)
        msg = formatter.format(record)

        _logger.opt(depth=depth, exception=record.exc_info).log(
            level, msg, type=record.name
        )


def get_log(type_name: str):
    return _logger.bind(type=type_name)


def init_logging():
    """
    初始化日志
    Returns:

    """
    log_format = env(
        "LOGURU_FORMAT",
        str,
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<red>{extra[type]: <10}</red> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    _logger.remove()
    _logger.add(sys.stdout, colorize=True, format=log_format)

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)
