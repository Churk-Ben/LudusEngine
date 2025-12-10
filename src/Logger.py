# ------------------------------
# @author: Churk
# @description: 日志模块
# @completed
# ------------------------------

import functools
import inspect
import logging
import os
from pathlib import Path

from concurrent_log_handler import ConcurrentRotatingFileHandler

BASE = Path(__file__).resolve().parent.parent
LOG_DIR = BASE / "logs"
DEFAULT_LOGFILE = LOG_DIR / "ludus.log"

FORMATTER = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S"
)

os.makedirs(LOG_DIR, exist_ok=True)


def _create_stream_handler(level):
    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(FORMATTER)
    return sh


def _create_file_handler(logfile, level):
    # 使用大小轮转日志文件，每个文件最大100KB，保留5个备份
    # This is process-safe
    fh = ConcurrentRotatingFileHandler(
        logfile, maxBytes=102400, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(level)
    fh.setFormatter(FORMATTER)
    return fh


class DecoratorFactory:
    """
    一个工厂类, 用于创建日志装饰器, 并将其绑定到指定的日志记录器实例.
    例如, @logger.decorate.info("Executing {func_name}")
    """

    def __init__(self, logger):
        self._logger = logger

    def _create_decorator(self, level, message_template):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Bind arguments to parameter names for rich formatting
                bound_args = inspect.signature(func).bind(*args, **kwargs)
                bound_args.apply_defaults()

                # Create a dictionary of all arguments, including defaults
                all_args = bound_args.arguments

                # Add special and all-encompassing format keys
                format_dict = {
                    **all_args,
                    "func_name": func.__name__,
                    "args": args,
                    "kwargs": kwargs,
                }

                self._logger.log(level, message_template.format(*args, **format_dict))
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def info(self, message_template):
        """创建一个 INFO 级别的日志装饰器, 用于记录函数调用前的信息."""
        return self._create_decorator(logging.INFO, message_template)

    def debug(self, message_template):
        """创建一个 DEBUG 级别的日志装饰器, 用于记录函数调用前的调试信息."""
        return self._create_decorator(logging.DEBUG, message_template)

    def warning(self, message_template):
        """创建一个 WARNING 级别的日志装饰器, 用于记录函数调用前的警告信息."""
        return self._create_decorator(logging.WARNING, message_template)

    def error(self, message_template):
        """创建一个 ERROR 级别的日志装饰器, 用于记录函数调用前的错误信息."""
        return self._create_decorator(logging.ERROR, message_template)


def get_logger(name=None, level=logging.DEBUG, logfile=None):
    """
    返回配置好的日志记录器
    - name: 日志记录器名称 (默认根记录器) .
    - level: 日志级别 (默认 INFO) .
    - logfile: 日志文件路径. 若为 None 则使用 DEFAULT_LOGFILE .
    """
    if name is None:
        # 默认使用根包名, 如果无法获取则使用"Default"
        name = __package__ or "Default"

    logger = logging.getLogger(name)
    if logger.handlers:
        logger.setLevel(level)
        # 若记录器已配置过处理程序, 则直接返回
        if not hasattr(logger, "decorate"):
            setattr(logger, "decorate", DecoratorFactory(logger))
        return logger

    logfile = logfile or DEFAULT_LOGFILE

    logger.setLevel(level)
    logger.propagate = False

    logger.addHandler(_create_stream_handler(level))
    logger.addHandler(_create_file_handler(logfile, level))

    # 将 DecoratorFactory 实例绑定到记录器, 用于创建日志装饰器
    setattr(logger, "decorate", DecoratorFactory(logger))

    return logger


if __name__ == "__main__":
    # 测试日志记录器
    log = get_logger(name="testLogger", level=logging.DEBUG)

    @log.decorate.info("拉起函数 test, 参数 a={a}, b={b}")
    def test(a, b):
        log.info("函数 test 被调用")
        print(a + b)

    log.debug("这是一条调试信息")
    log.info("这是一条信息")
    log.warning("这是一条警告信息")
    log.error("这是一条错误信息")
    test(1, 2)
