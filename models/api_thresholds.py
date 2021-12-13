from sqlalchemy import Column, Integer, String, Float

from ...shared.db_manager import Base
from ...shared.models.abstract_base import AbstractBaseMixin


class APIThresholds(AbstractBaseMixin, Base):
    __tablename__ = "api_thresholds"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test = Column(String, unique=False, nullable=False)
    environment = Column(String, unique=False, nullable=False)
    scope = Column(String, unique=False, nullable=False)
    value = Column(Float, unique=False, nullable=False)
    target = Column(String, unique=False, nullable=False)
    aggregation = Column(String, unique=False, nullable=False)
    comparison = Column(String, unique=False, nullable=False)
