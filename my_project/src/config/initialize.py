# config/loader.py

from .config import Configuration
from .logger import setup_logger



def initialise():
    conf = Configuration()

    logger = setup_logger(conf.log)

    engine = None
    session = None

    # if conf.db.enable:
    #     engine, session = setup_db(conf.db)

    # if conf.nats.enable:
    #     conf.nats.validate()

    return conf, logger, engine, session