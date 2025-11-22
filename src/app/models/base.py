from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Float, Text, Date, Index
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from ...config.database import Base


class TimestampMixin:
    """
    Mixin for timestamp fields
    """
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=func.now(), nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=func.now(), onupdate=func.now(), nullable=True)


class BaseModel(Base):
    """
    Base model class
    """
    __abstract__ = True
