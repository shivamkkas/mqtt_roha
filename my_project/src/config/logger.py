# config/logger.py

import logging,os
from logging.handlers import RotatingFileHandler

from dotenv.main import logger


def setup_logger(conf):
    logger = logging.getLogger()
    if logger.handlers:
        return logger

    level = getattr(logging, conf.level.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    log_file = "log/app.log"

    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=conf.max_size * 1024 * 1024,
        backupCount=conf.max_age,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if conf.on_console:
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)
    logging.getLogger("uvicorn").handlers = logger.handlers
    logging.getLogger("uvicorn.error").handlers = logger.handlers
    logging.getLogger("uvicorn.access").handlers = logger.handlers

    return logger