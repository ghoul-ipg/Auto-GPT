import logging
import os

from flask.logging import has_level_handler, default_handler

LOG_DIR = "log/"
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)
LOG_FILENAME = LOG_DIR + "gpt_server.log"

FILE_HANDLER = logging.FileHandler(filename=LOG_FILENAME, mode='a', encoding='utf-8', delay=True)
FILE_HANDLER.setLevel(level=logging.DEBUG)
FILE_HANDLER.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s"))


def get_logger(name):
    """
    获取和flask server一致格式的logger
    :param name:
    :return:
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not has_level_handler(logger):
        logger.addHandler(default_handler)
    # add file logger to logger
    logger.addHandler(FILE_HANDLER)
    return logger
