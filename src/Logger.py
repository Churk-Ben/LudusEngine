# ------------------------------
# @author: Churk
# @description: 日志模块
# @not completed yet
# ------------------------------

import functools
import inspect
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from concurrent_log_handler import ConcurrentRotatingFileHandler

BASE = Path(__file__).resolve().parent.parent
LOG_DIR = BASE / "logs"
GAMES_DIR = BASE / ".games"
GAMES_LOG_DIR = GAMES_DIR / "logs"
DEFAULT_LOGFILE = LOG_DIR / "ludus.log"

FORMATTER = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S"
)
GAMES_LOG_FORMATTER = logging.Formatter("[%(asctime)s] %(message)s", "%m-%d %H:%M:%S")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(GAMES_LOG_DIR, exist_ok=True)


def _create_stream_handler(level, formatter=FORMATTER):
    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(formatter)
    return sh


def _create_file_handler(logfile, level, formatter=FORMATTER):
    # 使用大小轮转日志文件，每个文件最大100KB，保留5个备份
    # This is process-safe
    fh = ConcurrentRotatingFileHandler(
        logfile, maxBytes=102400, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(level)
    fh.setFormatter(formatter)
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


def get_logger(name=None, level=logging.DEBUG, logfile=None, formatter=FORMATTER):
    """
    返回配置好的日志记录器
    - name: 日志记录器名称 (默认根记录器) .
    - level: 日志级别 (默认 INFO) .
    - logfile: 日志文件路径. 若为 None 则使用 DEFAULT_LOGFILE .
    - formatter: 日志格式. 若为 None 则使用默认 FORMATTER .
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

    logger.addHandler(_create_stream_handler(level, formatter))
    logger.addHandler(_create_file_handler(logfile, level, formatter))

    # 将 DecoratorFactory 实例绑定到记录器, 用于创建日志装饰器
    setattr(logger, "decorate", DecoratorFactory(logger))

    return logger


class GameLogger:
    def __init__(self, name: str, players: List[Dict[str, str]]):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = GAMES_LOG_DIR / self.timestamp
        os.makedirs(self.log_dir, exist_ok=True)

        self._clear_handlers("System")
        self.system_logger = get_logger(
            "System", logging.INFO, self.log_dir / "System.log", GAMES_LOG_FORMATTER
        )

        self.loggers = {}
        for player in players:
            # Try to extract assuming {"player_uuid": "...", "player_name": "..."}
            p_uuid = player.get("player_uuid")
            p_name = player.get("player_name")

            # Fallback for {uuid: name} format
            if not p_uuid or not p_name:
                if len(player) == 1:
                    p_uuid = list(player.keys())[0]
                    p_name = list(player.values())[0]

            if p_uuid and p_name:
                self._clear_handlers(p_name)
                self.loggers[p_name] = get_logger(
                    p_name,
                    logging.INFO,
                    self.log_dir / f"{p_uuid}.log",
                    GAMES_LOG_FORMATTER,
                )

    def _clear_handlers(self, name):
        logger = logging.getLogger(name)
        for h in logger.handlers[:]:
            logger.removeHandler(h)
            h.close()

    def log_event(self, message: str, visible_to: List[str] = None):
        if visible_to:
            self.system_logger.info(f"[visible to {visible_to}] {message}")
            for p_name in visible_to:
                logger = self.loggers.get(p_name)
                if logger:
                    logger.info(message)
        else:
            self.system_logger.info(message)
            for logger in self.loggers.values():
                logger.info(message)

    def get_events(self, name):
        # 获得指定玩家的log文件路径
        return self.log_dir / f"{name}.log"

    def _get_player_log_file(self, name: str) -> Path:
        # 获得指定玩家的log文件路径
        return self.log_dir / f"{name}.log"


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
