"""SQLAlchemy 基类"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 PG ORM 模型的基类"""
    pass
