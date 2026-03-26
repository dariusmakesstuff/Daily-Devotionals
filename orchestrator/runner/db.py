import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from runner.config import get_settings
from runner import models_extended  # noqa: F401 — register extra tables on metadata
from runner.models import Base

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        url = get_settings().database_url
        kwargs: dict = {"pool_pre_ping": True}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(url, **kwargs)
    return _engine


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())
    logger.info("Database tables ensured (create_all).")
    factory = get_session_factory()
    with factory() as session:
        from runner.db_seed import seed_database

        seed_database(session)


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db():
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()
