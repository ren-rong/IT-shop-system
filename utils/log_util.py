"""日志工具：同时输出到控制台和 logs/test_run.log，留存请求/响应/环境信息。"""
import logging
import os

from utils.config_loader import ROOT_DIR


def get_logger(name="api_auto"):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    log_dir = os.path.join(ROOT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    fh = logging.FileHandler(os.path.join(log_dir, "test_run.log"), encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


logger = get_logger()
