# config/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def setup_db(conf):
    url = (
        f"postgresql://{conf.user}:{conf.password}"
        f"@{conf.host}:{conf.port}/{conf.name}"
    )

    engine = create_engine(
        url,
        pool_size=conf.open_connection,
        max_overflow=conf.idle_connection,
        pool_pre_ping=True,
    )

    SessionLocal = sessionmaker(bind=engine)

    return engine, SessionLocal